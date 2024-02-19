# MAAS Site Manager

This repository contains the MVP for the MAAS Site Manager. It contains one sub-folder for every sub-project.


## How to Run a Local Development Environment?

### Manual Setup

Please follow the instructions in [MAAS Site Manager Backend](/backend/README.md) and [MAAS Site Manager Frontend](/frontend/README.md).

### Using the snap

To build the snap run

```bash
snapcraft -v -o maas-site-manager.snap
```

The resulting snap can be installed via

```bash
sudo snap install --dangerous ./maas-site-manager.snap
```

After installation, the service won't be enabled automatically and need to be
configured.

The snap provides a few settings.

For database configuration:

- `db.host`: host to connect to (defaults: `localhost`)
- `db.port`: port to connect to (default: `5432`)
- `db.name`: database name (default: `msm`)
- `db.user`: database username (default: empty)
- `db.password`: database password (default: empty)

These can be set, after installing the snap via

```bash
sudo snap set maas-site-manager db.host=<hostname> db.name=<name> db.password=<password>
```

After setting the configuration, the service can be enabled

```bash
sudo snap start --enable maas-site-manager
```

Once the service is enabled, changing settings will automatically restart it
with the new ones.

### Using Docker Compose

Ensure that you have a recent version of [Docker](https://docs.docker.com/get-docker/) installed.

* Run `docker compose up --build` to start the backend and the database.
* Run `cd frontend` and `yarn dev` to start the frontend

#### A note on installing the frontend

As per default, `apt install yarn` installs `cmdtest`, a distinct package from the one we actually want to use. Instead, we recommend the following steps sourced from [yarn package](https://yarnpkg.com/):
```bash
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
```
The yarn package is now added as a source, so install as expected
```bash
sudo apt update && sudo apt install --no-install-recommends yarn
```
If not already installed, you'll also want NodeJS. We recommend using [nvm](https://github.com/nvm-sh/nvm) to accomplish this:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
```
NodeJS 16 is the minimum recommended version for MAAS-Site-Manager
```bash
nvm install 16
nvm use 16
```
After which you should be able to serve the frontend
```bash
cd frontend
yarn
yarn dev
```
