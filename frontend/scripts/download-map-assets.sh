#!/bin/bash

TILES_URL="https://github.com/canonical/natural-earth-pmtiles/raw/main/natural_earth.vector_v2.pmtiles"
TILES_PATH="public/natural_earth.vector_v2.pmtiles"

FONTS_URL="https://github.com/protomaps/basemaps-assets/archive/9fa7b36e3db2ed6b68aba1ffe848728b7cb2b4a2.zip"
FONTS_ZIP="basemaps-assets.zip"
FONTS_DIR="basemaps-assets-9fa7b36e3db2ed6b68aba1ffe848728b7cb2b4a2"
FONTS_PATH="public/assets/fonts/Noto Sans Regular"

process_fonts() {
    unzip $FONTS_ZIP
    if [ $? -ne 0 ]; then
        echo "Error unzipping $FONTS_ZIP"
        exit 1
    fi

    mkdir -p "$FONTS_PATH"
    cp -r "$FONTS_DIR/fonts/Noto Sans Regular/"* "$FONTS_PATH"
    if [ $? -ne 0 ]; then
        echo "Error copying fonts to $FONTS_PATH"
        exit 1
    fi

    rm $FONTS_ZIP
    rm -rf $FONTS_DIR
}

if [ -z "$(ls -A "$TILES_PATH")" ]; then
    curl -L "$TILES_URL" -o "$TILES_PATH"
fi

if [ -z "$(ls -A "$FONTS_PATH")" ]; then
    curl -L "$FONTS_URL" -o "$FONTS_ZIP"
    process_fonts
fi
