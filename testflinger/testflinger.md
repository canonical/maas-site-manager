# MSM Testflinger

This directory contains a testflinger definition and setup script. By submitting the testflinger job, testflinger will reserve a machine and:

- Install the MSM Juju stack
- Install the `latest/edge` MAAS snap
- Create an image source in MSM
- Select the Noble armhf image
- Enroll MAAS with MSM

As a tester, it is then your responsibility to check that MAAS properly downloads the Noble amrhf image. You can log into the MAAS instance by first checking the IP address of the machine in TOR3 MAAS. The machine name is noted by the `job_queue` in `testflinger.yaml`.

Then, head to `$MACHINE_IP:5240` and login with `admin` username and password.

## Running MSM Testflinger

To run a testflinger job, first update `testflinger/testflinger.yaml` with your LP username and uncomment the `reserve_data` section so that you can SSH to the machine after the setup. You need to do this even if you do not plan to SSH to the machine so that the machine is kept online after the testflinger job is finished. Then, cd to this directory (`testflinger`) and run `testflinger submit testflinger.yaml`. You can monitor the status of the job with `testflinger poll $JOB_ID`, where `JOB_ID` is the ID output by `testflinger submit`.

Once your testing is finished, you can `Ctrl-C` the `testflinger poll` command and it will ask you if you would like to cancel the job and release the machine. Select yes so anyone else that wishes to use this machine may do so.
