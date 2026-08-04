import argparse
import sys
from .processor import GeoelectricPostprocessor

def main():
    parser = argparse.ArgumentParser(
        description="Convert NOAA/SWPC-USGS Geoelectric Field Model NetCDF outputs to GeoJSON/ASCII exchange formats."
    )

    parser.add_argument(
        "in_dir",
        help="Path to an input .nc file or a directory containing .nc files."
    )
    parser.add_argument(
        "-o", "--out-dir",
        default=None,
        help="Output directory for exported files (defaults to <in_dir>/output)."
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "geojson", "ascii", "dat"],
        default="json",
        help="Output format choice: 'json' or 'ascii' (default: json)."
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Start time filter in ISO format (e.g., 'YYYY-MM-DDThh:mm:ss')."
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End time filter in ISO format (e.g., 'YYYY-MM-DDThh:mm:ss')."
    )

    args = parser.parse_args()

    try:
        processor = GeoelectricPostprocessor(
            in_dir=args.in_dir,
            out_dir=args.out_dir,
            output_format=args.format,
            start_time=args.start,
            end_time=args.end,
        )
        processor.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
