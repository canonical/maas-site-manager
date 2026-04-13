from datetime import timedelta
import re
from typing import Any, ClassVar, Generic, TypeVar
from urllib.parse import urlparse

from netaddr import (  # type: ignore[import-untyped]
    AddrFormatError,
    IPAddress,
    IPNetwork,
)
from pydantic import (
    BaseModel,
    Field,
    IPvAnyAddress,
    field_validator,
)

from msm.common.enums import (
    DNSSEC,
    ActiveDiscoveryInterval,
    InterfaceLinkType,
    IPMICipherSuiteID,
    IPMIPrivilegeLevel,
    IPMIWorkaroundFlags,
    StorageLayout,
)

T = TypeVar("T")
LABEL = r"[a-zA-Z0-9]([-a-zA-Z0-9]{0,62}[a-zA-Z0-9]){0,1}"
NAMESPEC = rf"({LABEL}[.])*{LABEL}[.]?"
DEFAULT_OS = "ubuntu"
DEFAULT_OS_RELEASE = "noble"
# Time, in minutes, until the node times out during commissioning, testing,
# deploying, or entering rescue mode…
NODE_TIMEOUT = 30

# How often the import service runs.
IMPORT_RESOURCES_SERVICE_PERIOD = timedelta(hours=1)

_SYSTEMD_DURATION_RE = re.compile(
    r"((?P<hours>\d+?)(\s?(hour(s?)|hr|h))\s?)?((?P<minutes>\d+?)(\s?(minute(s?)|min|m))\s?)?((?P<seconds>\d+?)(\s?(second(s?)|sec|s))\s?)?"
)


def systemd_interval_to_seconds(interval: str) -> float:
    duration = _SYSTEMD_DURATION_RE.match(interval)
    if duration is None or not duration.group():
        raise ValueError(
            f"'{interval}' is not a valid interval. Only 'h|hr|hour|hours, m|min|minute|minutes."
            f"s|sec|second|seconds' are valid units"
        )
    params = {name: int(t) for name, t in duration.groupdict().items() if t}
    return timedelta(**params).total_seconds()


def validate_domain_name(name: str) -> None:
    """Validator for domain names.

    :param name: Input value for a domain name.  Must not include hostname.
    :raise ValidationError: If the domain name is not valid according to
    RFCs 952 and 1123.
    """
    # Valid characters within a hostname label: ASCII letters, ASCII digits,
    # hyphens.
    # Technically we could write all of this as a single regex, but it's not
    # very good for code maintenance.
    label_chars = re.compile("[a-zA-Z0-9-]*$")

    if len(name) > 255:
        raise ValueError(
            "Hostname is too long.  Maximum allowed is 255 characters."
        )
    # A hostname consists of "labels" separated by dots.
    labels = name.split(".")
    for label in labels:
        if len(label) == 0:
            raise ValueError("DNS name contains an empty label.")
        if len(label) > 63:
            raise ValueError(
                f"Label is too long: {label}.  Maximum allowed is 63 characters."
            )
        if label.startswith("-") or label.endswith("-"):
            raise ValueError(
                f"Label cannot start or end with hyphen: {label}."
            )
        if not label_chars.match(label):
            raise ValueError(f"Label contains disallowed characters: {label}.")


def validate_hostname(hostname: str) -> None:
    """Validator for hostnames.

    :param hostname: Input value for a hostname.  May include domain.
    :raise ValidationError: If the hostname is not valid according to RFCs 952
        and 1123.
    """
    # Valid characters within a hostname label: ASCII letters, ASCII digits,
    # hyphens, and underscores.  Not all are always valid.
    # Technically we could write all of this as a single regex, but it's not
    # very good for code maintenance.

    if len(hostname) > 255:
        raise ValueError(
            "Hostname is too long.  Maximum allowed is 255 characters."
        )
    # A hostname consists of "labels" separated by dots.
    host_part = hostname.split(".")[0]
    if "_" in host_part:
        # The host label cannot contain underscores; the rest of the name can.
        raise ValueError(f"Host label cannot contain underscore: {host_part}.")
    validate_domain_name(hostname)


def splithost(host: str) -> tuple[str | None, int | None]:
    """Split `host` into hostname and port.

    If no :port is in `host` the port with return as None.
    """
    parsed = urlparse("//" + host)
    hostname = parsed.hostname
    if hostname is None:
        # This only occurs when the `host` is an IPv6 address without brakets.
        # Lets try again but add the brackets.
        parsed = urlparse(f"//[{host}]")
        hostname = parsed.hostname
    if hostname is not None and ":" in hostname:
        # IPv6 hostname, place back into brackets.
        hostname = f"[{hostname}]"
    return hostname, parsed.port


class SiteConfig(BaseModel, Generic[T]):
    name: ClassVar[str]
    description: ClassVar[str]
    help_text: ClassVar[str | None] = None
    default: ClassVar
    value: T


class ThemeConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "theme"
    default: ClassVar[str | None] = ""
    description: ClassVar[str] = "MAAS theme"
    value: str | None = Field(default=default, description=description)


class KernelOptsConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "kernel_opts"
    default: ClassVar[str | None] = None
    description: ClassVar[str] = (
        "Boot parameters to pass to the kernel by default"
    )
    value: str | None = Field(default=default, description=description)


class MAASProxyPortConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "maas_proxy_port"
    default: ClassVar[int | None] = 8000
    description: ClassVar[str] = (
        "Port to bind the MAAS built-in proxy (default: 8000)"
    )
    help_text: ClassVar[str | None] = (
        "Defines the port used to bind the built-in proxy. The default port is 8000."
    )
    value: int | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_port(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value > 65535 or value <= 0:
            raise ValueError(
                "Unable to change port number. Port number is not between 0 - 65535."
            )
        if value >= 0 and value <= 1023:
            raise ValueError(
                "Unable to change port number. Port number is reserved for system services."
            )
        # 5239-5240 -> reserved for region HTTP.
        # 5241 - 4247 -> reserved for other MAAS services.
        # 5248 -> reserved for rack HTTP.
        # 5250 - 5270 -> reserved for region workers (RPC).
        # 5271 - 5274 -> reserved for communication between Rack Controller (specifically maas-agent) and Region Controller.
        # 5281 - 5284 -> Region Controller Temporal cluster membership gossip communication.
        if value >= 5239 and value <= 5284:
            raise ValueError(
                "Unable to change port number. Port number is reserved for MAAS services."
            )
        return value


class UsePeerProxyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "use_peer_proxy"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Use the built-in proxy with an external proxy as a peer"
    )
    help_text: ClassVar[str | None] = (
        "If enable_http_proxy is set, the built-in proxy will be configured to use http_proxy as a peer proxy. The deployed machines will be configured to use the built-in proxy."
    )
    value: bool | None = Field(default=default, description=description)


class PreferV4ProxyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "prefer_v4_proxy"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Sets IPv4 DNS resolution before IPv6"
    help_text: ClassVar[str | None] = (
        "If prefer_v4_proxy is set, the proxy will be set to prefer IPv4 DNS resolution before it attempts to perform IPv6 DNS resolution."
    )
    value: bool | None = Field(default=default, description=description)


class DefaultDnsTtlConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "default_dns_ttl"
    default: ClassVar[int | None] = 30
    description: ClassVar[str] = "Default Time-To-Live for the DNS"
    help_text: ClassVar[str | None] = (
        "If no TTL value is specified at a more specific point this is how long DNS responses are valid, in seconds."
    )
    value: int | None = Field(default=default, description=description)


class UpstreamDnsConfig(SiteConfig[list[IPvAnyAddress] | None]):
    name: ClassVar[str] = "upstream_dns"
    default: ClassVar[list[IPvAnyAddress] | None] = None
    description: ClassVar[str] = (
        "Upstream DNS used to resolve domains not managed by this MAAS (space-separated IP addresses)"
    )
    help_text: ClassVar[str | None] = (
        "Only used when MAAS is running its own DNS server. This value is used as the value of 'forwarders' in the DNS server config."
    )
    value: list[IPvAnyAddress] | None = Field(
        default=default, description=description
    )


class DNSSECValidationConfig(SiteConfig[DNSSEC | None]):
    name: ClassVar[str] = "dnssec_validation"
    default: ClassVar[DNSSEC | None] = DNSSEC.AUTO
    description: ClassVar[str] = "Enable DNSSEC validation of upstream zones"
    help_text: ClassVar[str | None] = (
        "Only used when MAAS is running its own DNS server. This value is used as the value of 'dnssec_validation' in the DNS server config."
    )
    value: DNSSEC | None = Field(default=default, description=description)


class MAASInternalDomainConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "maas_internal_domain"
    default: ClassVar[str | None] = "maas-internal"
    description: ClassVar[str] = (
        "Domain name used by MAAS for internal mapping of MAAS provided services."
    )
    help_text: ClassVar[str | None] = (
        "This domain should not collide with an upstream domain provided by the set upstream DNS."
    )
    value: str | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        namespec = re.compile(f"^{NAMESPEC}$")
        if not namespec.search(value) or len(value) > 255:
            raise ValueError(f"Invalid domain name: {value}.")
        return value


class DNSTrustedAclConfig(SiteConfig[str | None]):
    """Accepts a space/comma separated list of hostnames, Subnets or IPs.

    This field normalizes the list to a space-separated list.
    """

    _separators = re.compile(r"[,\s]+")
    _pt_ipv4 = r"(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    _pt_ipv6 = r"(?:([0-9A-Fa-f]{1,4})?[:]([0-9A-Fa-f]{1,4})?[:](.*))"
    _pt_ip = re.compile(rf"^({_pt_ipv4}|{_pt_ipv6})$", re.VERBOSE)
    _pt_subnet = re.compile(rf"^({_pt_ipv4}|{_pt_ipv6})/\d+$", re.VERBOSE)

    name: ClassVar[str] = "dns_trusted_acl"
    default: ClassVar[str | None] = None
    description: ClassVar[str] = (
        "List of external networks (not previously known), that will be allowed to use MAAS for DNS resolution."
    )
    help_text: ClassVar[str | None] = (
        "MAAS keeps a list of networks that are allowed to use MAAS for DNS resolution. This option allows to add extra networks (not previously known) to the trusted ACL where this list of networks is kept. It also supports specifying IPs or ACL names."
    )
    value: str | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        values = map(str.strip, cls._separators.split(value))
        values_not_empty = (value for value in values if len(value) != 0)
        clean_values = map(cls._clean_addr_or_host, values_not_empty)
        return " ".join(clean_values)

    @classmethod
    def _clean_addr_or_host(cls, value: str) -> str:
        if cls._pt_subnet.match(value):  # Looks like subnet
            return cls._clean_subnet(value)
        elif cls._pt_ip.match(value):  # Looks like ip
            return cls._clean_addr(value)
        else:  # Anything else
            return cls._clean_host(value)

    @classmethod
    def _clean_addr(cls, value: str) -> str:
        try:
            return str(IPAddress(value))
        except (ValueError, AddrFormatError) as e:
            raise ValueError(f"Invalid IP address: {value}.") from e

    @classmethod
    def _clean_subnet(cls, value: str) -> str:
        try:
            return str(IPNetwork(value))
        except AddrFormatError as e:
            raise ValueError(f"Invalid network: {value}.") from e

    @classmethod
    def _clean_host(cls, host: str) -> str:
        try:
            validate_hostname(host)
        except ValueError as e:
            raise ValueError(f"Invalid hostname: {e!s}") from e
        return host


class AllowOnlyTrustedTransfersConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "allow_only_trusted_transfers"
    default: ClassVar[bool] = True
    description: ClassVar[str] = "Allow only trusted zone transfers"
    help_text: ClassVar[str | None] = (
        "A boolean value to allow only zone transfers from trusted sources. If set to false, zone transfers from all sources will be allowed"
    )
    value: bool | None = Field(default=default, description=description)


class RemoteSyslogConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "remote_syslog"
    default: ClassVar[str | None] = None
    description: ClassVar[str] = "Remote syslog server to forward machine logs"
    help_text: ClassVar[str | None] = (
        "A remote syslog server that MAAS will set on enlisting, commissioning, testing, and deploying machines to send all log messages. Clearing this value will restore the default behaviour of forwarding syslog to MAAS."
    )
    value: str | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        if not value:
            return None
        host, port = splithost(value)
        if not port:
            port = 514
        return f"{host}:{port}"


class MAASSyslogPortConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "maas_syslog_port"
    default: ClassVar[int | None] = 5247
    description: ClassVar[str] = (
        "Port to bind the MAAS built-in syslog (default: 5247)"
    )
    help_text: ClassVar[str | None] = (
        "Defines the port used to bind the built-in syslog. The default port is 5247."
    )
    value: int | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_port(cls, value: int | None) -> int | None:
        if value is None:
            return None
        # Allow the internal syslog port
        if value == 5247:
            return value
        if value > 65535 or value <= 0:
            raise ValueError(
                "Unable to change port number. Port number is not between 0 - 65535."
            )
        if value >= 0 and value <= 1023:
            raise ValueError(
                "Unable to change port number. Port number is reserved for system services."
            )
        # 5239-5240 -> reserved for region HTTP.
        # 5241 - 4247 -> reserved for other MAAS services.
        # 5248 -> reserved for rack HTTP.
        # 5250 - 5270 -> reserved for region workers (RPC).
        # 5271 - 5274 -> reserved for communication between Rack Controller (specifically maas-agent) and Region Controller.
        # 5281 - 5284 -> Region Controller Temporal cluster membership gossip communication.
        if value >= 5239 and value <= 5284:
            raise ValueError(
                "Unable to change port number. Port number is reserved for MAAS services."
            )
        return value


class ActiveDiscoveryIntervalConfig(
    SiteConfig[ActiveDiscoveryInterval | None]
):
    name: ClassVar[str] = "active_discovery_interval"
    default: ClassVar[ActiveDiscoveryInterval | None] = (
        ActiveDiscoveryInterval.EVERY_3_HOURS
    )
    description: ClassVar[str] = "Active subnet mapping interval"
    help_text: ClassVar[str | None] = (
        "When enabled, each rack will scan subnets enabled for active mapping. This helps ensure discovery information is accurate and complete."
    )
    value: ActiveDiscoveryInterval | None = Field(
        default=default, description=description
    )


class DefaultBootInterfaceLinkTypeConfig(SiteConfig[InterfaceLinkType | None]):
    name: ClassVar[str] = "default_boot_interface_link_type"
    default: ClassVar[InterfaceLinkType | None] = InterfaceLinkType.AUTO
    description: ClassVar[str] = "Default boot interface IP Mode"
    help_text: ClassVar[str | None] = (
        "IP Mode that is applied to the boot interface on a node when it is commissioned."
    )
    value: InterfaceLinkType | None = Field(
        default=default, description=description
    )


class DefaultOSystemConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "default_osystem"
    default: ClassVar[str | None] = DEFAULT_OS
    description: ClassVar[str] = "Default operating system used for deployment"
    help_text: ClassVar[str | None] = ""
    value: str | None = Field(default=default, description=description)

    # TODO ADD VALIDATION


class DefaultDistroSeriesConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "default_distro_series"
    default: ClassVar[str | None] = DEFAULT_OS_RELEASE
    description: ClassVar[str] = "Default OS release used for deployment"
    help_text: ClassVar[str | None] = ""
    value: str | None = Field(default=default, description=description)

    # TODO ADD VALIDATION


class DefaultMinHweKernelConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "default_min_hwe_kernel"
    default: ClassVar[str | None] = ""
    description: ClassVar[str] = "Default Minimum Kernel Version"
    help_text: ClassVar[str | None] = (
        "The default minimum kernel version used on all new and commissioned nodes."
    )
    value: str | None = Field(default=default, description=description)

    # TODO ADD VALIDATION


class EnableKernelCrashDumpConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enable_kernel_crash_dump"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Enable the kernel crash dump feature in deployed machines."
    )
    help_text: ClassVar[str | None] = (
        "Enable the collection of kernel crash dump when a machine is deployed."
    )
    value: bool | None = Field(default=default, description=description)


class DefaultStorageLayoutConfig(SiteConfig[StorageLayout | None]):
    name: ClassVar[str] = "default_storage_layout"
    default: ClassVar[StorageLayout | None] = StorageLayout.FLAT
    description: ClassVar[str] = "Default storage layout"
    help_text: ClassVar[str | None] = (
        "Storage layout that is applied to a node when it is commissioned."
    )
    value: StorageLayout | None = Field(
        default=default, description=description
    )


class CommissioningDistroSeriesConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "commissioning_distro_series"
    default: ClassVar[str | None] = DEFAULT_OS_RELEASE
    description: ClassVar[str] = (
        "Default Ubuntu release used for commissioning"
    )
    help_text: ClassVar[str | None] = ""
    value: str | None = Field(default=default, description=description)

    # TODO ADD VALIDATION


class EnableThirdPartyDriversConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enable_third_party_drivers"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Enable the installation of proprietary drivers (i.e. HPVSA)"
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class EnableDiskErasingOnReleaseConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enable_disk_erasing_on_release"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Erase nodes' disks prior to releasing"
    help_text: ClassVar[str | None] = (
        "Forces users to always erase disks when releasing."
    )
    value: bool | None = Field(default=default, description=description)


class DiskEraseWithSecureEraseConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "disk_erase_with_secure_erase"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Use secure erase by default when erasing disks"
    )
    help_text: ClassVar[str | None] = (
        "Will only be used on devices that support secure erase.  Other devices will fall back to full wipe or quick erase depending on the selected options."
    )
    value: bool | None = Field(default=default, description=description)


class DiskEraseWithQuickEraseConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "disk_erase_with_quick_erase"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Use quick erase by default when erasing disks."
    )
    help_text: ClassVar[str | None] = (
        "This is not a secure erase; it wipes only the beginning and end of each disk."
    )
    value: bool | None = Field(default=default, description=description)


class BootImagesAutoImportConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "boot_images_auto_import"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        f"Automatically import/refresh the boot images every {IMPORT_RESOURCES_SERVICE_PERIOD.total_seconds() / 60.0} minutes"
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class BootImagesNoProxyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "boot_images_no_proxy"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Set no_proxy with the image repository address when MAAS is behind (or set with) a proxy."
    )
    help_text: ClassVar[str | None] = (
        "By default, when MAAS is behind (and set with) a proxy, it is used to download images from the image repository. In some situations (e.g. when using a local image repository) it doesn't make sense for MAAS to use the proxy to download images because it can access them directly. Setting this option allows MAAS to access the (local) image repository directly by setting the no_proxy variable for the MAAS env with the address of the image repository."
    )
    value: bool | None = Field(default=default, description=description)


class CurtinVerboseConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "curtin_verbose"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Run the fast-path installer with higher verbosity. This provides more detail in the installation logs"
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class ForceV1NetworkYamlConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "force_v1_network_yaml"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Always use the legacy v1 YAML (rather than Netplan format, also known as v2 YAML) when composing the network configuration for a machine."
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class EnableAnalyticsConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enable_analytics"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Enable Google Analytics in MAAS UI to shape improvements in user experience"
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class CompletedIntroConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "completed_intro"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = (
        "Marks if the initial intro has been completed"
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class MaxNodeCommissioningResultsConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "max_node_commissioning_results"
    default: ClassVar[int | None] = 10
    description: ClassVar[str] = (
        "The maximum number of commissioning results runs which are stored"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class MaxNodeTestingResultsConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "max_node_testing_results"
    default: ClassVar[int | None] = 10
    description: ClassVar[str] = (
        "The maximum number of testing results runs which are stored"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class MaxNodeInstallationResultsConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "max_node_installation_results"
    default: ClassVar[int | None] = 3
    description: ClassVar[str] = (
        "The maximum number of installation result runs which are stored"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class MaxNodeReleaseResultsConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "max_node_release_results"
    default: ClassVar[int | None] = 3
    description: ClassVar[str] = (
        "The maximum number of release result runs which are stored"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class MaxNodeDeploymentResultsConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "max_node_deployment_results"
    default: ClassVar[int | None] = 3
    description: ClassVar[str] = (
        "The maximum number of deployment result runs which are stored"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class SubnetIPExhaustionThresholdCountConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "subnet_ip_exhaustion_threshold_count"
    default: ClassVar[int | None] = 16
    description: ClassVar[str] = (
        "If the number of free IP addresses on a subnet becomes less than or equal to this threshold, an IP exhaustion warning will appear for that subnet"
    )
    help_text: ClassVar[str | None] = ""
    value: int | None = Field(default=default, description=description, ge=1)


class ReleaseNotificationsConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "release_notifications"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Enable or disable notifications for new MAAS releases."
    )
    help_text: ClassVar[str | None] = ""
    value: bool | None = Field(default=default, description=description)


class UseRackProxyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "use_rack_proxy"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Use DNS and HTTP metadata proxy on the rack controllers when a machine is booted."
    )
    help_text: ClassVar[str | None] = (
        "All DNS and HTTP metadata traffic will flow through the rack controller that a machine is booting from. This isolated region controllers from machines."
    )
    value: bool | None = Field(default=default, description=description)


class NodeTimeoutConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "node_timeout"
    default: ClassVar[int | None] = NODE_TIMEOUT
    description: ClassVar[str] = (
        "Time, in minutes, until the node times out during commissioning, testing, deploying, or entering rescue mode."
    )
    help_text: ClassVar[str | None] = (
        "Commissioning, testing, deploying, and entering rescue mode all set a timeout when beginning. If MAAS does not hear from the node within the specified number of minutes the node is powered off and set into a failed status."
    )
    value: int | None = Field(default=default, description=description, ge=1)


class PrometheusEnabledConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "prometheus_enabled"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Enable Prometheus exporter"
    help_text: ClassVar[str | None] = (
        "Whether to enable Prometheus exporter functions, including Cluster metrics endpoint and Push gateway (if configured)."
    )
    value: bool | None = Field(default=default, description=description)


class PrometheusPushGatewayConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "prometheus_push_gateway"
    default: ClassVar[str | None] = None
    description: ClassVar[str] = (
        "Address or hostname of the Prometheus push gateway."
    )
    help_text: ClassVar[str | None] = (
        "Defines the address or hostname of the Prometheus push gateway where MAAS will send data to."
    )
    value: str | None = Field(default=default, description=description)


class PrometheusPushIntervalConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "prometheus_push_interval"
    default: ClassVar[int | None] = 60
    description: ClassVar[str] = (
        "Interval of how often to send data to Prometheus (default: to 60 minutes)."
    )
    help_text: ClassVar[str | None] = (
        "The internal of how often MAAS will send stats to Prometheus in minutes."
    )
    value: int | None = Field(default=default, description=description)


class PromtailEnabledConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "promtail_enabled"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Enable streaming logs to Promtail."
    help_text: ClassVar[str | None] = "Whether to stream logs to Promtail"
    value: bool | None = Field(default=default, description=description)


class PromtailPortConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "promtail_port"
    default: ClassVar[int | None] = 5238
    description: ClassVar[str] = "TCP port of the Promtail Push API."
    help_text: ClassVar[str | None] = (
        "Defines the TCP port of the Promtail push API where MAAS will stream logs to."
    )
    value: int | None = Field(default=default, description=description)


class EnlistCommissioningConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enlist_commissioning"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Whether to run commissioning during enlistment."
    )
    help_text: ClassVar[str | None] = (
        "Enables running all built-in commissioning scripts during enlistment."
    )
    value: bool | None = Field(default=default, description=description)


class MAASAutoIPMIUserConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "maas_auto_ipmi_user"
    default: ClassVar[str | None] = "maas"
    description: ClassVar[str] = "MAAS IPMI user."
    help_text: ClassVar[str | None] = (
        "The name of the IPMI user that MAAS automatically creates during enlistment/commissioning."
    )
    value: str | None = Field(default=default, description=description)


class MAASAutoIPMIUserPrivilegeLevelConfig(
    SiteConfig[IPMIPrivilegeLevel | None]
):
    name: ClassVar[str] = "maas_auto_ipmi_user_privilege_level"
    default: ClassVar[IPMIPrivilegeLevel | None] = IPMIPrivilegeLevel.ADMIN
    description: ClassVar[str] = "MAAS IPMI privilege level"
    help_text: ClassVar[str | None] = (
        "The default IPMI privilege level to use when creating the MAAS user and talking IPMI BMCs"
    )
    value: IPMIPrivilegeLevel | None = Field(
        default=default, description=description
    )


class MAASAutoIPMICipherSuiteIDConfig(SiteConfig[IPMICipherSuiteID | None]):
    name: ClassVar[str] = "maas_auto_ipmi_cipher_suite_id"
    default: ClassVar[IPMICipherSuiteID | None] = IPMICipherSuiteID.SUITE_3
    description: ClassVar[str] = "MAAS IPMI Default Cipher Suite ID"
    help_text: ClassVar[str | None] = (
        "The default IPMI cipher suite ID to use when connecting to the BMC via ipmitools"
    )
    value: IPMICipherSuiteID | None = Field(
        default=default, description=description
    )


class MAASAutoIPMIWorkaroundFlagsConfig(
    SiteConfig[list[IPMIWorkaroundFlags] | None]
):
    name: ClassVar[str] = "maas_auto_ipmi_workaround_flags"
    default: ClassVar[list[IPMIWorkaroundFlags] | None] = None
    description: ClassVar[str] = "IPMI Workaround Flags"
    help_text: ClassVar[str | None] = (
        "The default workaround flag (-W options) to use for ipmipower commands"
    )
    value: list[IPMIWorkaroundFlags] | None = Field(
        default=default, description=description
    )


class NTPServersConfig(SiteConfig[str | None]):
    """Accepts a space/comma separated list of hostnames or IP addresses.

    This field normalizes the list to a space-separated list.
    """

    _separators = re.compile(r"[,\s]+")

    # Regular expressions to sniff out things that look like IP addresses;
    # additional and more robust validation ought to be done to make sure.
    _pt_ipv4 = r"(?: \d{1,3} [.] \d{1,3} [.] \d{1,3} [.] \d{1,3} )"
    _pt_ipv6 = rf"(?: (?: [\da-fA-F]+ :+)+ (?: [\da-fA-F]+ | {_pt_ipv4} )+ )"
    _pt_ip = re.compile(rf"^ (?: {_pt_ipv4} | {_pt_ipv6} ) $", re.VERBOSE)

    name: ClassVar[str] = "ntp_servers"
    hook_required: ClassVar[bool] = True
    default: ClassVar[str | None] = "ntp.ubuntu.com"
    description: ClassVar[str] = "Addresses of NTP servers"
    help_text: ClassVar[str | None] = (
        "NTP servers, specified as IP addresses or hostnames delimited by commas and/or spaces, to be used as time references for MAAS itself, the machines MAAS deploys, and devices that make use of MAAS's DHCP services."
    )
    value: str | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        else:
            values = map(str.strip, cls._separators.split(value))
            values_not_empty = (value for value in values if len(value) != 0)
            clean_values = map(cls._clean_addr_or_host, values_not_empty)
            return " ".join(clean_values)

    @classmethod
    def _clean_addr_or_host(cls, value: str) -> str:
        looks_like_ip = cls._pt_ip.match(value) is not None
        if looks_like_ip:
            return cls._clean_addr(value)
        elif ":" in value:
            # This is probably an IPv6 address. It's definitely not a
            # hostname.
            return cls._clean_addr(value)
        else:
            return cls._clean_host(value)

    @classmethod
    def _clean_addr(cls, addr: str) -> str:
        try:
            addr = IPAddress(addr)
        except AddrFormatError as error:
            message = str(error)  # netaddr has good messages.
            message = f"{message[:1].upper()}{message[1:]}."
            raise ValueError(message)
        else:
            return str(addr)

    @classmethod
    def _clean_host(cls, host: str) -> str:
        try:
            validate_hostname(host)
        except ValueError as error:
            raise ValueError(f"Invalid hostname: {error!s}")
        else:
            return host


class NTPExternalOnlyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "ntp_external_only"
    hook_required: ClassVar[bool] = True
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Use external NTP servers only"
    help_text: ClassVar[str | None] = (
        "Configure all region controller hosts, rack controller hosts, and subsequently deployed machines to refer directly to the configured external NTP servers. Otherwise only region controller hosts will be configured to use those external NTP servers, rack contoller hosts will in turn refer to the regions' NTP servers, and deployed machines will refer to the racks' NTP servers."
    )
    value: bool | None = Field(default=default, description=description)


class HardwareSyncIntervalConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "hardware_sync_interval"
    default: ClassVar[str | None] = "15m"
    description: ClassVar[str] = "Hardware Sync Interval"
    help_text: ClassVar[str | None] = (
        "The interval to send hardware info to MAAS fromhardware sync enabled machines, in systemd time span syntax."
    )
    value: str | None = Field(default=default, description=description)

    @field_validator("value")
    @classmethod
    def validate_systemd_interval(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # try to parse the interval.
        systemd_interval_to_seconds(value)
        return value


class TlsCertExpirationNotificationEnabledConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "tls_cert_expiration_notification_enabled"
    default: ClassVar[bool | None] = False
    description: ClassVar[str] = "Notify when the certificate is due to expire"
    help_text: ClassVar[str | None] = (
        "Enable/Disable notification about certificate expiration."
    )
    value: bool | None = Field(default=default, description=description)


class TLSCertExpirationNotificationIntervalConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "tls_cert_expiration_notification_interval"
    default: ClassVar[int | None] = 30
    description: ClassVar[str] = "Certificate expiration reminder (days)"
    help_text: ClassVar[str | None] = (
        "Configure notification when certificate is due to expire in (days)."
    )
    value: int | None = Field(
        default=default, description=description, ge=1, le=90
    )


class SessionLengthConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "session_length"
    hook_required: ClassVar[bool] = True
    default: ClassVar[int | None] = 1209600
    description: ClassVar[str] = "Session timeout (seconds)"
    help_text: ClassVar[str | None] = (
        "Configure timeout of session (seconds). Minimum 10s, maximum 2 weeks (1209600s)."
    )
    value: int | None = Field(
        default=default, description=description, ge=10, le=1209600
    )


class RefreshTokenDurationConfig(SiteConfig[int | None]):
    name: ClassVar[str] = "refresh_token_duration"
    hook_required: ClassVar[bool] = True
    default: ClassVar[int | None] = 2592000  # 30 days
    description: ClassVar[str] = "Refresh token duration (seconds)"
    help_text: ClassVar[str | None] = (
        "Configure duration of refresh token (seconds). Minimum 10 minutes, maximum 60 days (5184000s)."
    )
    value: int | None = Field(
        default=default, description=description, ge=600, le=5184000
    )


class AutoVlanCreationConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "auto_vlan_creation"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Automatically create VLANs and Fabrics for interfaces"
    )
    help_text: ClassVar[str | None] = (
        "Enables the creation of a default VLAN and Fabric for discovered network interfaces when MAAS cannot connect it to an existing one. When disabled, the interface is left disconnected in these cases."
    )
    value: bool | None = Field(default=default, description=description)


class EnableHttpProxyConfig(SiteConfig[bool | None]):
    name: ClassVar[str] = "enable_http_proxy"
    default: ClassVar[bool | None] = True
    description: ClassVar[str] = (
        "Enable the use of an APT or YUM and HTTP/HTTPS proxy"
    )
    help_text: ClassVar[str | None] = (
        "Provision nodes to use the built-in HTTP proxy (or user specified proxy) for APT or YUM. MAAS also uses the proxy for downloading boot images."
    )
    value: bool | None = Field(default=default, description=description)


class WindowsKmsHostConfig(SiteConfig[str | None]):
    name: ClassVar[str] = "windows_kms_host"
    hook_required: ClassVar[bool] = True
    default: ClassVar[str | None] = None
    description: ClassVar[str] = "Windows KMS activation host"
    help_text: ClassVar[str | None] = (
        "FQDN or IP address of the host that provides the KMS Windows activation service. (Only needed for Windows deployments using KMS activation.)"
    )
    value: str | None = Field(default=default, description=description)


class SiteConfigFactory:
    # key/value pairs that are commented out exist in MAAS,
    # but cannot be set by Site Manager.
    ALL_CONFIGS: ClassVar[dict[str, type[SiteConfig[Any]]]] = {
        # MAASNameConfig.name: MAASNameConfig,
        ThemeConfig.name: ThemeConfig,
        KernelOptsConfig.name: KernelOptsConfig,
        EnableHttpProxyConfig.name: EnableHttpProxyConfig,
        # HttpProxyConfig.name: HttpProxyConfig,
        MAASProxyPortConfig.name: MAASProxyPortConfig,
        UsePeerProxyConfig.name: UsePeerProxyConfig,
        PreferV4ProxyConfig.name: PreferV4ProxyConfig,
        DefaultDnsTtlConfig.name: DefaultDnsTtlConfig,
        UpstreamDnsConfig.name: UpstreamDnsConfig,
        DNSSECValidationConfig.name: DNSSECValidationConfig,
        MAASInternalDomainConfig.name: MAASInternalDomainConfig,
        DNSTrustedAclConfig.name: DNSTrustedAclConfig,
        AllowOnlyTrustedTransfersConfig.name: AllowOnlyTrustedTransfersConfig,
        RemoteSyslogConfig.name: RemoteSyslogConfig,
        MAASSyslogPortConfig.name: MAASSyslogPortConfig,
        ActiveDiscoveryIntervalConfig.name: ActiveDiscoveryIntervalConfig,
        DefaultBootInterfaceLinkTypeConfig.name: DefaultBootInterfaceLinkTypeConfig,
        DefaultOSystemConfig.name: DefaultOSystemConfig,
        DefaultDistroSeriesConfig.name: DefaultDistroSeriesConfig,
        DefaultMinHweKernelConfig.name: DefaultMinHweKernelConfig,
        EnableKernelCrashDumpConfig.name: EnableKernelCrashDumpConfig,
        DefaultStorageLayoutConfig.name: DefaultStorageLayoutConfig,
        CommissioningDistroSeriesConfig.name: CommissioningDistroSeriesConfig,
        EnableThirdPartyDriversConfig.name: EnableThirdPartyDriversConfig,
        EnableDiskErasingOnReleaseConfig.name: EnableDiskErasingOnReleaseConfig,
        DiskEraseWithSecureEraseConfig.name: DiskEraseWithSecureEraseConfig,
        DiskEraseWithQuickEraseConfig.name: DiskEraseWithQuickEraseConfig,
        BootImagesAutoImportConfig.name: BootImagesAutoImportConfig,
        BootImagesNoProxyConfig.name: BootImagesNoProxyConfig,
        CurtinVerboseConfig.name: CurtinVerboseConfig,
        ForceV1NetworkYamlConfig.name: ForceV1NetworkYamlConfig,
        EnableAnalyticsConfig.name: EnableAnalyticsConfig,
        CompletedIntroConfig.name: CompletedIntroConfig,
        MaxNodeCommissioningResultsConfig.name: MaxNodeCommissioningResultsConfig,
        MaxNodeTestingResultsConfig.name: MaxNodeTestingResultsConfig,
        MaxNodeInstallationResultsConfig.name: MaxNodeInstallationResultsConfig,
        MaxNodeReleaseResultsConfig.name: MaxNodeReleaseResultsConfig,
        MaxNodeDeploymentResultsConfig.name: MaxNodeDeploymentResultsConfig,
        SubnetIPExhaustionThresholdCountConfig.name: SubnetIPExhaustionThresholdCountConfig,
        ReleaseNotificationsConfig.name: ReleaseNotificationsConfig,
        UseRackProxyConfig.name: UseRackProxyConfig,
        NodeTimeoutConfig.name: NodeTimeoutConfig,
        PrometheusEnabledConfig.name: PrometheusEnabledConfig,
        PrometheusPushGatewayConfig.name: PrometheusPushGatewayConfig,
        PrometheusPushIntervalConfig.name: PrometheusPushIntervalConfig,
        PromtailEnabledConfig.name: PromtailEnabledConfig,
        PromtailPortConfig.name: PromtailPortConfig,
        EnlistCommissioningConfig.name: EnlistCommissioningConfig,
        MAASAutoIPMIUserConfig.name: MAASAutoIPMIUserConfig,
        MAASAutoIPMIUserPrivilegeLevelConfig.name: MAASAutoIPMIUserPrivilegeLevelConfig,
        # MAASAutoIPMIKGBmcKeyConfig.name: MAASAutoIPMIKGBmcKeyConfig,
        MAASAutoIPMICipherSuiteIDConfig.name: MAASAutoIPMICipherSuiteIDConfig,
        MAASAutoIPMIWorkaroundFlagsConfig.name: MAASAutoIPMIWorkaroundFlagsConfig,
        NTPServersConfig.name: NTPServersConfig,
        NTPExternalOnlyConfig.name: NTPExternalOnlyConfig,
        # VCenterServerConfig.name: VCenterServerConfig,
        # VCenterUsernameConfig.name: VCenterUsernameConfig,
        # VCenterPasswordConfig.name: VCenterPasswordConfig,
        # VCenterDatacenterConfig.name: VCenterDatacenterConfig,
        HardwareSyncIntervalConfig.name: HardwareSyncIntervalConfig,
        # TODO: drop this when websocket will be removed (MAAS 4.0, hopefully).
        SessionLengthConfig.name: SessionLengthConfig,
        RefreshTokenDurationConfig.name: RefreshTokenDurationConfig,
        TlsCertExpirationNotificationEnabledConfig.name: TlsCertExpirationNotificationEnabledConfig,
        TLSCertExpirationNotificationIntervalConfig.name: TLSCertExpirationNotificationIntervalConfig,
        AutoVlanCreationConfig.name: AutoVlanCreationConfig,
        # Private configs.
        # ActiveDiscoveryLastScanConfig.name: ActiveDiscoveryLastScanConfig,
        # CommissioningOSystemConfig.name: CommissioningOSystemConfig,
        # MAASUrlConfig.name: MAASUrlConfig,
        # NetworkDiscoveryConfig.name: NetworkDiscoveryConfig,
        # OMAPIKeyConfig.name: OMAPIKeyConfig,
        # RPCSharedSecretConfig.name: RPCSharedSecretConfig,
        # TLSPortConfig.name: TLSPortConfig,
        # UUIDConfig.name: UUIDConfig,
        # VaultEnabledConfig.name: VaultEnabledConfig,
        WindowsKmsHostConfig.name: WindowsKmsHostConfig,
    }

    DEFAULT_CONFIG: ClassVar[dict[str, Any]] = {
        cfg_name: cfg_class.default
        for cfg_name, cfg_class in ALL_CONFIGS.items()
    }
