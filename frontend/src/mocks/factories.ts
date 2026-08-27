import Chance from "chance";
import { add, sub } from "date-fns";
import { Factory } from "fishery";
import { adjectives, animals, colors, starWars, uniqueNamesGenerator } from "unique-names-generator";

import type {
  AccessTokenResponse,
  BootSource,
  CallbackTargetResponse,
  GetV1SitesGetResponse,
  ImageSource,
  OidcProviderResponse,
  PendingSite,
  PendingSitesGetResponse,
  SelectableImage,
  SelectedImage,
  Settings,
  Site,
  SiteData,
  Token,
  User,
  UsersGetResponse,
} from "@/app/apiclient";
import { ConnectionStatus, OidcProviderAccessTokenType, TimeZone } from "@/app/apiclient";
import type { SiteMarkerType } from "@/app/sites/views/SitesMap/components/Map/types";

export const connections: ConnectionStatus[] = [
  ConnectionStatus.STABLE,
  ConnectionStatus.LOST,
  ConnectionStatus.UNKNOWN,
];

export const statsFactory = Factory.define<SiteData>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  const now = new Date();
  const machines = {
    machines_deployed: chance.integer({ min: 0, max: 500 }),
    machines_allocated: chance.integer({ min: 0, max: 500 }),
    machines_ready: chance.integer({ min: 0, max: 500 }),
    machines_error: chance.integer({ min: 0, max: 500 }),
    machines_other: chance.integer({ min: 0, max: 500 }),
  };
  return {
    ...machines,
    machines_total: Object.values(machines).reduce((acc, val) => acc + val, 0),
    last_seen: new Date(chance.date({ min: sub(now, { minutes: 15 }), max: now })).toISOString(),
  };
});

export const connectionFactory = Factory.define<Site["connection_status"]>(({ sequence }) => {
  return uniqueNamesGenerator({
    dictionaries: [connections],
    seed: sequence,
  }) as Site["connection_status"];
});

export const markerFactory = Factory.define<SiteMarkerType>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  return {
    id: sequence,
    position: [chance.latitude(), chance.longitude()],
  };
});

const coordinatesFactory = Factory.define<Site["coordinates"]>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  return { latitude: chance.latitude(), longitude: chance.longitude() };
});

export const siteFactory = Factory.define<NonNullable<Site>>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  const name = uniqueNamesGenerator({
    dictionaries: [adjectives, colors, animals],
    separator: "-",
    length: 2,
    seed: sequence,
  });

  const site = {
    id: sequence,
    name,
    name_unique: chance.bool(),
    url: `http://${name}.${chance.tld()}`,
    country: chance.country(), // <alpha2 country code>,
    city: chance.city(),
    note: "",
    region: null,
    coordinates: coordinatesFactory.build(),
    postal_code: chance.zip(),
    address: chance.address(),
    state: chance.province(),
    timezone: chance.pickone(Object.values(TimeZone)),
    connection_status: connectionFactory.build(),
    stats: statsFactory.build() as SiteData,
    cluster_uuid: chance.guid(),
  } as const;
  return site;
});

export const userFactory = Factory.define<User>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);

  const full_name = uniqueNamesGenerator({
    dictionaries: [starWars],
    length: 1,
    seed: sequence,
  });
  // .replace("é", "e") <-- This is to make sure usernames and email addresses are valid.
  const username = `${full_name.replace(/\s/g, "").replace("é", "e")}${chance.integer({ min: 1, max: 99 })}`;
  const email = `${username}@galactic-republic.gov`.toLowerCase().replace("é", "e");
  const is_admin = chance.bool();
  const id = sequence;

  return {
    full_name,
    username,
    email,
    is_admin,
    id,
  };
});

export const enrollmentRequestQueryResultFactory = Factory.define<PendingSitesGetResponse>(() => {
  return { items: [], total: 0, page: 0, size: 0 };
});
export const sitesQueryResultFactory = Factory.define<GetV1SitesGetResponse>(() => {
  return { items: [], total: 0, page: 0, size: 0 };
});
export const usersQueryResultFactory = Factory.define<UsersGetResponse>(() => {
  return { items: [], total: 0, page: 0, size: 0 };
});

export const durationFactory = Factory.define<string>(() => "P7DT0H0M0S");
export const tokenFactory = Factory.define<Token>(({ sequence }) => {
  const now = new Date();
  const chance = new Chance(`maas-${sequence}`);
  return {
    id: sequence,
    audience: chance.pickone(["maas", "maas-ui"]),
    purpose: chance.pickone(["access", "refresh"]),
    value: chance.hash({ length: 64 }),
    expired: new Date(
      chance.date({
        min: add(now, { seconds: 1 }),
        max: add(now, { days: 1 }),
      }),
    ).toISOString(), //<ISO 8601 date string>,
    created: new Date(chance.date({ min: sub(now, { minutes: 15 }), max: now })).toISOString(), //<ISO 8601 date string>
  };
});

export const accessTokenFactory = Factory.define<AccessTokenResponse>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  return {
    access_token: chance.hash({ length: 64 }),
    rotation_interval_minutes: 15,
    token_type: "bearer",
  };
});

export const callbackTargetFactory = Factory.define<CallbackTargetResponse>(() => {
  return {
    redirect_target: "/sites",
  };
});

export const oidcProviderFactory = Factory.define<OidcProviderResponse>(({ sequence }) => {
  const now = new Date();
  const chance = new Chance(`maas-${sequence}`);
  const issuerUrl = `https://${chance.word()}.example.com`;
  return {
    id: sequence,
    created: new Date(chance.date({ min: sub(now, { days: 30 }), max: now })).toISOString(),
    updated: new Date(chance.date({ min: sub(now, { days: 30 }), max: now })).toISOString(),
    name: `${chance.word()}-oidc`,
    client_id: chance.hash({ length: 32 }),
    client_secret: chance.hash({ length: 64 }),
    issuer_url: issuerUrl,
    redirect_uri: "http://localhost:3000/api/v1/external-auth/callback",
    scopes: "openid profile email",
    token_type: chance.pickone([OidcProviderAccessTokenType.JWT, OidcProviderAccessTokenType.OPAQUE]),
    enabled: true,
    metadata: {
      authorization_endpoint: `${issuerUrl}/authorize`,
      token_endpoint: `${issuerUrl}/token`,
      userinfo_endpoint: `${issuerUrl}/userinfo`,
      introspection_endpoint: `${issuerUrl}/introspect`,
      revocation_endpoint: `${issuerUrl}/revoke`,
      jwks_uri: `${issuerUrl}/.well-known/jwks.json`,
    },
    user_count: chance.integer({ min: 0, max: 100 }),
  };
});

export const enrollmentRequestFactory = Factory.define<PendingSite>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  const name = uniqueNamesGenerator({
    dictionaries: [adjectives, colors, animals],
    separator: "-",
    length: 2,
    seed: sequence,
  });
  return {
    id: sequence,
    cluster_uuid: chance.guid(),
    name,
    url: `http://${name}.${chance.tld()}`,
    created: new Date(chance.date({ year: 2023 })).toISOString(), //<ISO 8601 date string>
  };
});

// TODO: replace with actual Settings type
// once settings api is updated
// https://warthogs.atlassian.net/browse/MAASENG-2594
export const settingsFactory = Factory.define<Settings>(() => ({
  service_url: "http://localhost:3000",
  images_connect_to_maas: true,
}));

const ubuntuReleaseFactory = Factory.define<string>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  return chance.pickone(["23.10", "23.04", "22.10", "22.04 LTS"]);
});

const archFactory = Factory.define<string>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  return chance.pickone(["amd64", "arm64", "i386", "armhf"]);
});
const osFactory = Factory.define<{ name: string; release: string }>(({ sequence }) => {
  const chance = new Chance(`${sequence}`);
  return chance.pickone([
    { name: "ubuntu", release: ubuntuReleaseFactory.build() },
    { name: "centos", release: chance.pickone(["8", "7"]) },
    { name: "windows", release: chance.pickone(["10", "8.1", "7"]) },
    { name: "rhel", release: chance.pickone(["8", "7"]) },
    {
      name: "hannah montana linux",
      release: chance.pickone(["6.0.0", "7.0.0"]),
    },
  ]);
});

export const selectedImageFactory = Factory.define<SelectedImage>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);
  const OS = osFactory.build();
  const bootSource = imageSourceFactory.build();
  const size = chance.integer({ min: 300 * 1024, max: 4 * 1024 * 1024 }) * 1024;
  const isCustom = chance.bool();
  return {
    id: sequence,
    selection_id: !isCustom ? sequence : null,
    custom_image_id: isCustom ? sequence : null,
    boot_source_id: bootSource.id,
    boot_source_name: bootSource.name,
    boot_source_url: bootSource.url,
    os: OS.name,
    arch: archFactory.build(),
    release: OS.release,
    size: size,
    downloaded: Math.floor(Math.random() * size),
  };
});

export const selectableImageFactory = Factory.define<SelectableImage>(({ sequence }) => {
  const OS = osFactory.build();
  const bootSource = imageSourceFactory.build();
  return {
    selection_id: sequence,
    os: OS.name,
    release: OS.release,
    arch: archFactory.build(),
    boot_source_id: bootSource.id,
    boot_source_name: bootSource.name,
    boot_source_url: bootSource.url,
  };
});

export const alternativeImageFactory = Factory.define<ImageSource>(({ sequence }) => {
  const bootSource = imageSourceFactory.build();
  return {
    selection_id: sequence,
    id: bootSource.id,
    name: bootSource.name,
    url: bootSource.url,
  };
});

export const imageSourceFactory = Factory.define<BootSource>(({ sequence }) => {
  const chance = new Chance(`maas-${sequence}`);

  return {
    id: chance.integer({ min: 1, max: 100 }),
    url: chance.pickone([
      chance.url(),
      `https://images-${chance.word()}.maas.io`,
      `http://boot-source-${chance.word()}.domain.${chance.domain()}`,
    ]),
    keyring: chance.pickone(["none", "gpg", "gpg-keyring"]),
    name: chance.pickone(["Windows", "Ubuntu", "CentOS"]),
    sync_interval: chance.pickone([0, 60, 120, 300, 600]),
    priority: chance.integer({ min: 1, max: 10 }),
    last_sync: new Date(chance.date({ year: 2023 })).toISOString(),
  };
});
