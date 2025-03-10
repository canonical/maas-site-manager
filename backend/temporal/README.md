# MSM Temporal Worker Rock

This is a rock to be deployed with the [Temporal Worker charm](https://charmhub.io/temporal-worker-k8s).

## Build

To build the rock after changes have been made to workflows, `cd` to this directory and run `rockcraft pack`.

## Deploy

To deploy the temporal worker with the newly built rock, first upload the rock to the local docker registry:

```bash
rockcraft.skopeo --insecure-policy copy --dest-tls-verify=false \
   oci-archive:${ROCK_FILE_NAME}$ \
   docker://localhost:32000/temporal-worker-rock:latest
```

Then, deploy Temporal Worker K8s:

```bash
juju deploy temporal-worker-k8s --resource temporal-worker-image=localhost:32000/temporal-worker-rock:latest
```

### More Information

For more information, see the Temporal Worker K8s [GitHub page](https://github.com/canonical/temporal-worker-k8s-operator)
