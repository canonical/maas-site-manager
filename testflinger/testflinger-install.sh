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

echo "s3_endpoint = \"http://$MICROCEPH_IP:$MICROCEPH_PORT\"" > $HOME/msm-deployment/terraform.tfvars
echo "s3_access_key = \"$MICROCEPH_ACCESS_KEY\"" >> $HOME/msm-deployment/terraform.tfvars
echo "s3_secret_key = \"$MICROCEPH_SECRET_KEY\"" >> $HOME/msm-deployment/terraform.tfvars
echo "s3_bucket = \"$MICROCEPH_BUCKET\"" >> $HOME/msm-deployment/terraform.tfvars

cd $HOME/msm-deployment
terraform init
terraform apply -auto-approve > $HOME/terraform-output

HOST_IP=$(hostname -I | cut -d' ' -f1)
# install maas
sudo snap install maas --channel latest/edge
sudo snap install maas-test-db
echo "\n" | sudo maas init region+rack --database-uri maas-test-db:/// --maas-url="http://${HOST_IP}:5240/MAAS"
sudo maas createadmin --username admin --password admin --email admin@example.com

# Create MSM admin
juju run -m msm maas-site-manager-k8s/0 create-admin username=admin password=admin email=admin@example.com


# Add source to MSM

echo "############################"
echo "Creating image source"
echo "############################"
TOKEN=$(curl -d "username=admin@example.com&password=admin" \
-X POST http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/login \
| jq -r .access_token)

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer ${TOKEN}" \
  -d '{"priority": 10, "url": "http://images.maas.io/ephemeral-v3/candidate/streams/v1/index.json", "sync_interval": 1, "name": "Test Source", "keyring": ""}' \
  http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/bootasset-sources

# wait for source sync
echo "############################"
echo "Waiting for initial sync"
echo "############################"
sleep 75


NOBLE_ARM_SEL_ID=$(curl -H "Authorization: bearer ${TOKEN}" \
    http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/selectable-images \
    | jq '.items[] | select(.os == "ubuntu" and .release == "noble" and .arch == "armhf")' \
    | jq .selection_id)


echo "############################"
echo "Selecting Noble armhf (ID ${NOBLE_ARM_SEL_ID})"
echo "############################"

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer ${TOKEN}" \
  -d "{\"selection_ids\": [$NOBLE_ARM_SEL_ID]}" \
  http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/selectable-images:select



echo "############################"
echo "Enrolling MAAS with MSM"
echo "############################"

# enroll
ENROL_TOKEN=$(curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer ${TOKEN}" \
  -d '{"count": 1, "duration": "PT1H30M"}' \
  http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/tokens | jq -r .items[0].value)

sudo maas msm enrol $ENROL_TOKEN --yes

sleep 5

# get pending sites
SITE_ID=$(curl -H "Authorization: bearer ${TOKEN}" \
  http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/sites/pending \
  | jq -r .items[0].id)

# approve pending site
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer ${TOKEN}" \
  -d "{\"ids\": [$SITE_ID], \"accept\":true}" \
  http://${HOST_IP}/msm-maas-site-manager-k8s/api/v1/sites/pending
