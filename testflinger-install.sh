#!/bin/bash
sudo snap install juju --channel=3.6/stable
sudo snap install --classic terraform --channel latest/stable
sudo snap install microceph --channel latest/edge
sudo snap refresh --hold microceph
sudo microceph cluster bootstrap

export MICROCEPH_PORT=7887
export MICROCEPH_ACCESS_KEY=fooaccesskey
export MICROCEPH_SECRET_KEY=barsecretkey
export MICROCEPH_BUCKET=msm-images
sudo microceph disk add loop,40G,3
sudo microceph enable rgw --port $MICROCEPH_PORT
sudo radosgw-admin user create --uid=user --display-name=user
sudo radosgw-admin key create --uid=user --key-type=s3 --access-key=$MICROCEPH_ACCESS_KEY --secret-key=$MICROCEPH_SECRET_KEY
export MICROCEPH_IP=$(sudo microceph status | grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
sudo apt install -y s3cmd
s3cmd --host $MICROCEPH_IP:$MICROCEPH_PORT --host-bucket=http://$MICROCEPH_IP/$MICROCEPH_BUCKET --access_key=$MICROCEPH_ACCESS_KEY --secret_key=$MICROCEPH_SECRET_KEY --no-ssl mb s3://$MICROCEPH_BUCKET

sudo microk8s enable hostpath-storage
sudo microk8s enable ingress
IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
sudo microk8s enable metallb:$IPADDR-$IPADDR

juju bootstrap microk8s
export CONTROLLER=$(juju whoami | yq .Controller)
export JUJU_CONTROLLER_ADDRESSES=$(juju show-controller | yq .$CONTROLLER.details.api-endpoints | yq -r '. | join(",")')
export JUJU_USERNAME="$(cat ~/.local/share/juju/accounts.yaml | yq .controllers.$CONTROLLER.user|tr -d '"')"
export JUJU_PASSWORD="$(cat ~/.local/share/juju/accounts.yaml | yq .controllers.$CONTROLLER.password|tr -d '"')"
export JUJU_CA_CERT="$(juju show-controller $(echo $CONTROLLER|tr -d '"') | yq '.[$CONTROLLER]'.details.\"ca-cert\"|tr -d '"'|sed 's/\\n/\n/g')"
mkdir $HOME/msm-deployment
curl https://git.launchpad.net/maas-site-manager/plain/deployment/terraform/main.tf -o $HOME/msm-deployment/main.tf
curl https://git.launchpad.net/maas-site-manager/plain/deployment/terraform/provider.tf -o $HOME/msm-deployment/provider.tf
curl https://git.launchpad.net/maas-site-manager/plain/deployment/terraform/temporal.tf -o $HOME/msm-deployment/temporal.tf
curl https://git.launchpad.net/maas-site-manager/plain/deployment/terraform/variables.tf -o $HOME/msm-deployment/variables.tf

echo "s3_endpoint = \"$MICROCEPH_IP:$MICROCEPH_PORT\"" > $HOME/msm-deployment/terraform.tfvars
echo "s3_access_key = \"$MICROCEPH_ACCESS_KEY\"" >> $HOME/msm-deployment/terraform.tfvars
echo "s3_secret_key = \"$MICROCEPH_SECRET_KEY\"" >> $HOME/msm-deployment/terraform.tfvars
echo "s3_bucket = \"$MICROCEPH_BUCKET\"" >> $HOME/msm-deployment/terraform.tfvars

cd $HOME/msm-deployment
terraform init
terraform apply -auto-approve
