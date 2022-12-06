#!/usr/bin/env sh
#
# Creates items (with geoparquet) for all zipfiles in a given directory.
#
# Usage:
#
#   scripts/create_items.sh data/
#
# Items and geoparquet files will be created alongside the zip files.
# If you'd like to download all FWS NWI data, use the `stac fws-nwi download` command line utility.

set -e

indir=$1
outdir=$2

if [ -z "$indir" ] || [ -z "$outdir" ]; then
    echo "Error: invalid usage"
    echo "USAGE: scripts/create_item.sh indir outdir"
    exit 1
fi

for path in "$indir"/*.zip; do
    outfile="$outdir/${path##*/}"
    outfile="${outfile%.zip}/item.json"
    mkdir -p "$(dirname $outfile)"
    if [ -f $outfile ]; then
        echo "$outfile already exists, skipping..."
        continue
    else
        echo "Creating $outfile..."
    fi
    stac fws-nwi create-item --create-geoparquet "$path" "$outfile"
done
