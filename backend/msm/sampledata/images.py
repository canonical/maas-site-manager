from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncConnection

from msm.sampledata.db import (
    ModelCollection,
    SampleDataModel,
)


async def make_fixture_images(conn: AsyncConnection) -> list[SampleDataModel]:
    collection = ModelCollection("boot_source")
    collection.add(
        priority=1,
        url="http://some.image.server",
        keyring="""-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBFxEQeMBCACtgu58j4RuE34OW3Xoy4PIXlLv/8P+FUUFs8Dk4WO5zUJN2NfN
45fIASdKcH8cV2wbCVwjKEP0h4p5IE+lrwQK7bwYx7Qt+qmrm5eLMUM8IvXA18wf
AOPS7XeKTzxa4/jWagJupmmYL+MuV9o5haqYplOYCcVR135KAZfx743YuWcNqvcr
3Em0+gh4F2TXsefjniwuJRGY3Kbb/MAM2zC2f7FfCJVb1C30OLB+KwCddZP/23ll
nOqmzaVF0qQrHQ5EZGK3j3S4fzHNq14TMS3c21YkPOO/DV6BkgIHtG5NIIdVEdQh
wV8clpj0ZP7ShIE8cDhTy8k+xrIByPUVfpMpABEBAAG0J0JpbGwgQnVjaGFuYW4g
PHcuYnVjaGFuYW5AbmFwaWVyLmFjLnVrPokBVAQTAQgAPhYhBK9cqX/wEcCpQ6+5
TFPDJcqRPXoQBQJcREHjAhsDBQkDwmcABQsJCAcCBhUKCQgLAgQWAgMBAh4BAheA
AAoJEFPDJcqRPXoQ2KIH/2sRAsqbrqCMNMRsiBo9XtCFzQ052odbzubIScnwzrDF
Y9z+qPSAwaWGO+1R3LPDH5sMLQ2YOsNqg8VvTJBtOjR9YGNX9/bqqVFRKKSQ0HiD
Sb2M7phBdk4WLkqLZ/AfgHaLKpfNX0bq7WhqZ+Pez0nqjN08JkIog7LhaQZh/Chf
0pl+wHV0rEFuaDQn83yF5DWB1Dt4fbzfVUrEJb92tSrReHALQQA3h5WkTA0qxhDd
9XyEWknDrYCWIWoj0XWjiVUre2fw3SKn8KHvJDeDYVKzYy18oA+da+xgs9b+n+Tq
mMlfslWhw9wRyp0jbVLEs3yxLgE4elbCCmgiTNpnmMW5AQ0EXERB4wEIAKCPJqmM
o8m6Xm163XtAZnx3t02EJSAV6u0yINIC8aEudNWg+/ptKKanUDm38dPnOl1mgOyC
FEu4qFJHbMidkEEac5J0lgvhRK7jv94KF3vxqKr/bYnxltghqCfXesga9jfAHV8J
M6sx4exOoc+/52YskpvDUs/eTPnWoQnbgjP+wsZpNq0owS6yO5urDfD6lvefgK5A
TfB9lQUE0lpb6IMKkcBZZvpZWOchbwPWCB9JZMuirDSyksuTLdqgEsW7MyKBjCae
E/THuTazumad/PyEb0RCbODdMb55L6CD2W2DUquVBLI9FN6KTYWk5L/JzNAIWBV9
TKfevup933j1m+sAEQEAAYkBPAQYAQgAJhYhBK9cqX/wEcCpQ6+5TFPDJcqRPXoQ
BQJcREHjAhsMBQkDwmcAAAoJEFPDJcqRPXoQGRgH/3592g1F4+WRaPbuCgfEMihd
ma5gplU2J7NjNbV9IcY8VZsGw7UAT7FfmTPqlvwFM3w3gQCDXCKGztieUkzMTPqb
LujBR4y55d5xDY6mP40zwRgdRlen2XsgHLPajRQpAhZq8ZvOdGe/ANCyXVdFHbGy
aFAMUfAhxkbITQKXH+EIkCHXDtDUHUxmAQvsZ8Z+Jm+ZwdhWkMsK43tw8UXLIynp
AeOoATdohke3EVK5+0Dc/jezcUWz2IKfw7LB3sQ4c6H8Ey8PThlNAIgwMCDp5WTB
DmFoRWTU6CpKtwIg/lb1ncbslH2xAFeUX6ASHXR8vBOnIXWss21FuAaNmWe4lmw=
=S+hs
-----END PGP PUBLIC KEY BLOCK-----""",
        sync_interval=3600,
    )
    collection.add(
        priority=2,
        url="http://another.image.server",
        keyring="""-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBFxEQeMBCACtgu58j4RuE34OW3Xoy4PIXlLv/8P+FUUFs8Dk4WO5zUJN2NfN
45fIASdKcH8cV2wbCVwjKEP0h4p5IE+lrwQK7bwYx7Qt+qmrm5eLMUM8IvXA18wf
AOPS7XeKTzxa4/jWagJupmmYL+MuV9o5haqYplOYCcVR135KAZfx743YuWcNqvcr
3Em0+gh4F2TXsefjniwuJRGY3Kbb/MAM2zC2f7FfCJVb1C30OLB+KwCddZP/23ll
nOqmzaVF0qQrHQ5EZGK3j3S4fzHNq14TMS3c21YkPOO/DV6BkgIHtG5NIIdVEdQh
wV8clpj0ZP7ShIE8cDhTy8k+xrIByPUVfpMpABEBAAG0J0JpbGwgQnVjaGFuYW4g
PHcuYnVjaGFuYW5AbmFwaWVyLmFjLnVrPokBVAQTAQgAPhYhBK9cqX/wEcCpQ6+5
TFPDJcqRPXoQBQJcREHjAhsDBQkDwmcABQsJCAcCBhUKCQgLAgQWAgMBAh4BAheA
AAoJEFPDJcqRPXoQ2KIH/2sRAsqbrqCMNMRsiBo9XtCFzQ052odbzubIScnwzrDF
Y9z+qPSAwaWGO+1R3LPDH5sMLQ2YOsNqg8VvTJBtOjR9YGNX9/bqqVFRKKSQ0HiD
Sb2M7phBdk4WLkqLZ/AfgHaLKpfNX0bq7WhqZ+Pez0nqjN08JkIog7LhaQZh/Chf
0pl+wHV0rEFuaDQn83yF5DWB1Dt4fbzfVUrEJb92tSrReHALQQA3h5WkTA0qxhDd
9XyEWknDrYCWIWoj0XWjiVUre2fw3SKn8KHvJDeDYVKzYy18oA+da+xgs9b+n+Tq
mMlfslWhw9wRyp0jbVLEs3yxLgE4elbCCmgiTNpnmMW5AQ0EXERB4wEIAKCPJqmM
o8m6Xm163XtAZnx3t02EJSAV6u0yINIC8aEudNWg+/ptKKanUDm38dPnOl1mgOyC
FEu4qFJHbMidkEEac5J0lgvhRK7jv94KF3vxqKr/bYnxltghqCfXesga9jfAHV8J
M6sx4exOoc+/52YskpvDUs/eTPnWoQnbgjP+wsZpNq0owS6yO5urDfD6lvefgK5A
TfB9lQUE0lpb6IMKkcBZZvpZWOchbwPWCB9JZMuirDSyksuTLdqgEsW7MyKBjCae
E/THuTazumad/PyEb0RCbODdMb55L6CD2W2DUquVBLI9FN6KTYWk5L/JzNAIWBV9
TKfevup933j1m+sAEQEAAYkBPAQYAQgAJhYhBK9cqX/wEcCpQ6+5TFPDJcqRPXoQ
BQJcREHjAhsMBQkDwmcAAAoJEFPDJcqRPXoQGRgH/3592g1F4+WRaPbuCgfEMihd
ma5gplU2J7NjNbV9IcY8VZsGw7UAT7FfmTPqlvwFM3w3gQCDXCKGztieUkzMTPqb
LujBR4y55d5xDY6mP40zwRgdRlen2XsgHLPajRQpAhZq8ZvOdGe/ANCyXVdFHbGy
aFAMUfAhxkbITQKXH+EIkCHXDtDUHUxmAQvsZ8Z+Jm+ZwdhWkMsK43tw8UXLIynp
AeOoATdohke3EVK5+0Dc/jezcUWz2IKfw7LB3sQ4c6H8Ey8PThlNAIgwMCDp5WTB
DmFoRWTU6CpKtwIg/lb1ncbslH2xAFeUX6ASHXR8vBOnIXWss21FuAaNmWe4lmw=
=S+hs
-----END PGP PUBLIC KEY BLOCK-----""",
        sync_interval=7200,
    )

    boot_sources = await collection.create(conn)

    collection = ModelCollection("boot_source_selection")
    collection.add(
        boot_source_id=boot_sources[0].id,
        label="stable",
        os="Ubuntu",
        release="24.04",
        arches=["amd64"],
    )
    collection.add(
        boot_source_id=boot_sources[1].id,
        label="candidate",
        os="Ubuntu",
        release="22.04",
        arches=["amd64", "arm"],
    )

    await collection.create(conn)

    collection = ModelCollection("boot_asset")
    collection.add(
        boot_source_id=boot_sources[0].id,
        kind=0,
        label="stable",
        os="Ubuntu",
        release="24.04",
        codename="Noble Numbat",
        title="Ubuntu Noble",
        arch="amd64",
        subarch="generic",
        compatibility=["generic"],
        flavor="generic",
        base_image="Ubuntu",
        eol=datetime(2029, 4, 1, tzinfo=UTC),
        esm_eol=datetime(2036, 4, 1, tzinfo=UTC),
    )

    collection.add(
        boot_source_id=boot_sources[0].id,
        kind=0,
        label="candidate",
        os="Ubuntu",
        release="22.04",
        codename="Jammy Jellyfish",
        title="Ubuntu Jammy",
        arch="amd64",
        subarch="generic",
        compatibility=["generic"],
        flavor="generic",
        base_image="Ubuntu",
        eol=datetime(2027, 4, 1, tzinfo=UTC),
        esm_eol=datetime(2034, 4, 1, tzinfo=UTC),
    )

    boot_assets = await collection.create(conn)

    collection = ModelCollection("boot_asset_version")
    collection.add(boot_asset_id=boot_assets[0].id, version="20240401.1")
    collection.add(boot_asset_id=boot_assets[1].id, version="20220401.1")

    boot_asset_versions = await collection.create(conn)

    collection = ModelCollection("boot_asset_item")
    collection.add(
        boot_asset_version_id=boot_asset_versions[0].id,
        ftype="kernel",
        sha256=sha256().hexdigest(),
        path="ubuntu/noble",
        size=3635135734,
        source_package="ubukernel",
        source_version="2.3.6",
        source_release="Noble",
        bytes_synced=3635135734,
    )
    collection.add(
        boot_asset_version_id=boot_asset_versions[0].id,
        ftype="kernel",
        sha256=sha256().hexdigest(),
        path="ubuntu/jammy",
        size=3655135734,
        source_package="ubukernel",
        source_version="2.2.6",
        source_release="Jammy",
        bytes_synced=3635135734,
    )
    await collection.create(conn)
    return boot_assets


async def purge_images(conn: AsyncConnection) -> None:
    """Delete all tokens"""
    await ModelCollection("boot_asset_item").purge(conn)
    await ModelCollection("boot_asset_version").purge(conn)
    await ModelCollection("boot_asset").purge(conn)
    await ModelCollection("boot_source_selection").purge(conn)
    await ModelCollection("boot_source").purge(conn)
