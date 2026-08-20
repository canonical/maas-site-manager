# MAAS Site Manager Development Tools

This document descibes various tools and tricks to use when developing MAAS Site Manager.
For how to get a development environment setup, see the [deployment docs](docs/deployment.md).
For a guide on how to update your development environment with your latest changes, see the [development docs](docs/development.md)

## Linting and testing

The project uses `tox` for running Python-related workflows.

- code formatting: `tox -e format`
- linting: `tox -e lint`
- type checking: `tox -e check`

Unit tests use `pytest`. Tests can be run using,

```bash
tox run -e test
```

or alternatively just,

```bash
tox
```

since this is the default target. This runs all tests in parallel, and reports coverage.

To run the tests sequentially, possibly selecting a subset of them, it is possible to use the default `py` environment passing additional arguments to `pytest`:

```bash
tox run -e py -- <extra args> ..
```

## Database Migrations

Database migrations are managed using [Alembic](https://alembic.sqlalchemy.org). The command is available through the `alembic` tox environment.

To ensure that the database is up to date with the changes in migrations, run,

```bash
tox run -e alembic -- upgrade head
```

When table definitions are changed, you can create a new patch by running,

```bash
tox run -e alembic -- revision --autogenerate -m $name
```

where `$name` is the desired migration name. The resulting filename will be of the form `$id_$name.py`, where the revision id is automatically incremented from the last one (note that, for this reason, passing `--rev-id` won't have any effect).

The `--autogenerate` parameter can be omitted to create an empty migration which can later be manually edited.

**NB** the database should be at the correct state previous to the modifications that the path should contain. This should be done by calling the env with `upgrade head` before generating new revisions.

### Fixing Existing Databases After Migration Squash

If you have an existing database from before the migration squash, you need to mark it as compatible with the new squashed migration. The database schema itself doesn't need changes - only the migration history tracking needs to be updated.

**Using alembic (recommended):**

```bash
tox run -e alembic -- stamp head
```

**For remote databases (manual SQL approach):**

If you cannot run the alembic command directly (e.g., for remote production databases), you can manually update the migration tracking table:

```sql
-- Delete old migration history
DELETE FROM alembic_version;

-- Insert the new squashed migration revision
INSERT INTO alembic_version (version_num) VALUES ('0000');
```

This achieves the same result as `alembic stamp head` by directly updating the Alembic version tracking table. After running either approach, future migrations will work normally.

## Manual setup on your host or on a virtual machine

The recommended way to develop MAAS Site Manager is in a charmed environment. If you wish to instead run MAAS Site Manager manually, follow the steps below. Note that this is not recommended.

The application is currently supported on Ubuntu 24.04 (Noble Numbat).

The following steps are needed for basic setup, after ensuring you are in the right directory (`/backend`):

- ensure make is installed

```bash
sudo apt install make
```

- install project dependencies

```bash
make install-dependencies
```

The application is run using the `uvicorn` ASGI server. It requires a postgres database to connect to. Having installed the (system-wide) PostgreSQL instance with `make install-dependencies`, the required user and database can be set up as follows:

- create new user with password

```bash
sudo -i -u postgres psql -c "CREATE USER \"msm\" WITH ENCRYPTED PASSWORD 'msm'"
sudo -i -u postgres createdb -O "msm" "msm"
```

- edit `pg_hba.conf` (under e.g. `/etc/postgres/14/main/`) to include at the bottom

```txt
host    msm     msm     0/0     md5
```

- restart postgres

```bash
sudo systemctl restart postgresql
```

- deploy Temporal and an S3 storage service

- export the following environment variables

```
MSM_DB_HOST=${POSTGRES_HOST}
MSM_DB_PORT=${POSTGRES_PORT}
MSM_DB_NAME=${POSTGRES_DB}
MSM_DB_USER=${POSTGRES_USER}
MSM_DB_PASSWORD=${POSTGRES_PASSWORD}
MSM_TEMPORAL_SERVER_ADDRESS=$TEMPORAL_IP:7233
MSM_TEMPORAL_NAMESPACE=my_temporal_ns
MSM_TEMPORAL_TASK_QUEUE=my_temporal_q
MSM_S3_ACCESS_KEY=my_access_key
MSM_S3_SECRET_KEY=my_secret_key
MSM_S3_ENDPOINT=http://$CEPH_IP:$CEPH_PORT
MSM_S3_BUCKET=my_s3_bucket
```

Then, the application can be run using

```bash
tox run -e api
```

A database schema is created for you on application startup. If the schema changes or you want a fresh start, you can do the following.

- empty and recreate the database

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

### Sample data

There is sample data available for testing. To load this, do the following:

- run `tox run -e sampledata -- create-fixtures`

If you used the test data, you can generate a token for the pre-existing `admin` user with,

```bash
export TOKEN=$(curl -X 'POST' 'http://localhost:8000/api/v1/login' -H 'accept: application/json' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin@example.com&password=admin' | jq -r .access_token)
```

and then call the endpoints with,

```bash
curl http://localhost:8000/api/v1/sites -H "Authorization: bearer $TOKEN"
```

### Other settings

There are other settings, configurable by setting environment variables, to control behaviours of the app.

- heartbeat interval: the time interval at which MSM expects its connected sites to send heartbeat. This is configurable as,

```bash
export MSM_HEARTBEAT_INTERVAL_SEC=<value>
```

in seconds. The default value is 300s.

- connection lost threshold: threshold value for which a site gets marked as 'connection lost' in MSM. This is configurable as,

```bash
export MSM_CONN_LOST_THRESHOLD_SEC=<value>
```

in seconds. The default value is 600s. Note that the connection lost threshold has to be greater than the heartbeat interval.

- metrics refresh interval: the time interval at which MSM metrics are refreshed. This is configurable as,

```bash
export MSM_METRICS_REFRESH_INTVAL_SEC=<value>
```

in seconds. The default value is 300s.

### API specification and documentation

The OpenAPI specification, and the corresponding Swagger UI listing of the available endpoints can be accessed through
`http://localhost:8000/api/openapi.json` and `http://localhost:8000/api/docs` respectively, assuming the backend is
being hosted locally.

## Frontend

- When installing the frontend for the first time, read the _note on installing the frontend_ below. Prerequisite steps for running anything with yarn (starting frontend, testing, etc.) are:

```bash
cd frontend
yarn
```

after which you can start the frontend (`yarn dev`).
Note that when running a local setup, it is not advised to run `make ci-dep`, since, depending on the host system, this might install outdated dependencies and cause issues.

### A note on installing the frontend

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

NodeJS 20 is the minimum recommended version for MAAS Site Manager

```bash
nvm install 20
nvm use 20
```

After which you should be able to serve the frontend

```bash
cd frontend
yarn
yarn dev
```

### Updating API Client

You can update TypeScript API Client from the OpenAPI schema by running the following command. Make sure that the backend is running beforehand.

```bash
yarn generate-api-client
```

### Using a local backend

Setup local environment variables

```bash
cp .env.development .env.development.local
```

Set `VITE_USE_MOCK_DATA` to `false` in `.env.development.local` and start the backend

### Project conventions

#### CSS

##### Mobile-first approach

We first write CSS styles specifically for mobile devices, and then progressively enhance them for larger screen sizes using min-width media queries.

Single and consistent direction of media queries (min-width) makes the code easier to read and maintain.

### Testing

We use [Cypress](https://www.cypress.io/) for end-to-end tests and [Vitest](https://vitest.dev/) for unit/integration tests. We prefer integration testing over unit testing as we focus on user-centric testing and avoid testing implementation details. That makes changes and refactoring easier and helps ensure that things continue to work as expected for the end user.

#### How to run tests

##### end-to-end

```bash
yarn cypress-run
```

##### unit/integration

```bash
yarn test
```

### Keeping packages up-to-date

Run `yarn upgrade-all` to attempt to upgrade all packages to latest version.

### Map assets

#### Fonts

Noto Sans fonts in pbf format compatible with MapLibre GL JS (located in `/frontend/public/`) are sourced from [protomaps](https://github.com/protomaps/basemaps-assets/tree/main/fonts).

#### Tiles

Natural Earth Vector tiles sourced from <https://github.com/lukasmartinelli/naturalearthtiles/releases/download/v1.0/natural_earth.vector.mbtiles> are converted to pmtiles using <https://github.com/protomaps/PMTiles>.
