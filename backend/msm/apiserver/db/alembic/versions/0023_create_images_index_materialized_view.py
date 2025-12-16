"""create images_index materialized view

Revision ID: 0023
Revises: 0022
Create Date: 2025-02-19 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Create the materialized view
    op.execute(
        """
        CREATE MATERIALIZED VIEW images_index AS
        SELECT DISTINCT ON (asset.boot_source_id, ver_item.ftype, ver_item.path)
            asset.id,
            asset.boot_source_id,
            asset.kind,
            asset.label,
            asset.os,
            asset.arch,
            asset.release,
            asset.asset_version,
            asset.krel,
            asset.codename,
            asset.title,
            asset.subarch,
            asset.compatibility,
            asset.flavor,
            asset.base_image,
            asset.bootloader_type,
            asset.eol,
            asset.esm_eol,
            asset.signed,
            ver_item.version,
            ver_item.ftype,
            ver_item.sha256,
            ver_item.path,
            ver_item.file_size,
            ver_item.bytes_synced,
            ver_item.source_package,
            ver_item.source_version,
            ver_item.source_release
        FROM
            (
                SELECT DISTINCT ON (boot_asset.os, boot_asset.release, boot_asset.arch)
                    source.priority,
                    boot_asset.id,
                    boot_asset.boot_source_id,
                    boot_asset.kind,
                    boot_asset.label,
                    boot_asset.os,
                    boot_asset.arch,
                    boot_asset.release,
                    boot_asset.version AS asset_version,
                    boot_asset.krel,
                    boot_asset.codename,
                    boot_asset.title,
                    boot_asset.subarch,
                    boot_asset.compatibility,
                    boot_asset.flavor,
                    boot_asset.base_image,
                    boot_asset.bootloader_type,
                    boot_asset.eol,
                    boot_asset.esm_eol,
                    boot_asset.signed
                FROM
                    (
                        boot_asset
                        JOIN
                        (
                            SELECT bs.id, bs.priority
                            FROM boot_source bs
                        ) AS source
                        ON boot_asset.boot_source_id = source.id
                    )
                ORDER BY boot_asset.os, boot_asset.release, boot_asset.arch, source.priority DESC
            ) as asset
        JOIN
            (
                (
                    SELECT DISTINCT ON (v.boot_asset_id) v.id, v.version, v.boot_asset_id
                    FROM boot_asset_version v
                    ORDER BY v.boot_asset_id, v.version DESC
                ) AS ver
                JOIN boot_asset_item item
                ON ver.id = item.boot_asset_version_id
            ) as ver_item
        ON ver_item.boot_asset_id = asset.id
        """
    )

    # Create the unique index
    op.execute(
        """
        CREATE UNIQUE INDEX image_item ON images_index (os, release, arch, path)
        """
    )


def downgrade() -> None:
    # Drop the index first
    op.execute("DROP INDEX IF EXISTS image_item")

    # Drop the materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS images_index")
