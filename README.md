# Geoelectric Postprocessing - File Format Conversion

Conversion of geoelectric field output form netCDF to JSON and ASCII files.

## Description

This package ingests daily netCDF files from the NOAA-USGS Geoelectric Field Model (https://www.spaceweather.gov/products/geoelectric-field-models-1-minute) and produces geoJSON or ASCII files at one minute cadence.

Retrospective simulations (i.e., science quality) using the NOAA-USGS Geoelectric models have been performed for the selected major geomagnetic storms. NetCDF files can be found here: https://testbed.spaceweather.gov/products/major-storm-geoelectric-simulations

NetCDf files from the real-time geoelectric model can be found here: https://services.swpc.noaa.gov/netcdf/geoelectric/. (Real time output can have unexpected artifacts from the geomagnetic data, use discretion.)

## Requirements

- netCDF4 >=1.6.0
- certifi
- cftime
- numpy >=1.21.2

## Installation

```shell
pip install git+ssh://git@github.com/NOAA-SWPC/geoelectric-python-postprocessor.git
```

## Usage

This command line will find and process ALL netCDF files inside the input directory (in_dir) and create json files (default) in the output directory (out_dir):

```shell
swpc-geoelectric path/to/in_dir -o path/to/out_dir
```

This python script allows you select the output format (json or ascii) and a custom time range:

```shell
from swpc_geoelectric import GeoelectricPostprocessor

processor = GeoelectricPostprocessor(
    in_dir="path/to/in_dir",
    out_dir="path/to/out_dir",        # Optional: defaults to <in_dir>/output
    output_format="json",            # Options: 'json' (default) or 'ascii'
    start_time='YYYY-MM-DDT00:00',   # Optional if not entire file is to be processed
    end_time='YYYY-MM-DDT00:00'
)

processor.run()
```

## Development Roadmap

- Specify singular location to receive time-series output
- Specify latitude and longitude bounds to reduce output footprint

## Contact

* Jordan Guerra <jordan.guerra@noaa.gov>
* Adam Kubaryk <adam.kubaryk@noaa.gov>

