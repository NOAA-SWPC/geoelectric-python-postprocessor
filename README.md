# Geoelectric Postprocessing - File Format Conversion

Conversion of geoelectric netCDF output into JSON and ASCII files.

## Description

Package ingests daily netCDF files from the NOAA-USGS Geoelectric Field Model and write out minute geoJSON or ASCII files.

Retrospective simulations (i.e., science quality) using the NOAA-USGS Geoelectric models have been performed for the selected major geomagnetic storms. NetCDF files can be found here: https://dev-01-alb-testbed-swpc.woc.noaa.gov/exercises/BES-2026/major-storm-geoelectric-simulations.

NetCDf files from the real-time geoelectric model can be found here: https://services.swpc.noaa.gov/netcdf/geoelectric/. (Real time output can have unexpected artifacts from the geomagnetic data, use discretion.)

## Requirements

- Python X
- 

## Installation

```shell
pip install git+ssh://git@gitlab-licensed.vlab.noaa.gov:29418/NWS/Operations/NCEP/SWPC/regional-geoelectric/geoelectric-python-postprocessor.git
```

## Usage

```shell
swpc-geoelectric path/to/in_dir -o path/to_out_dir
```

```shell
from swpc_geoelectric import GeoelectricPostprocessor

processor = GeoelectricPostprocessor(
    in_dir="path/to/netcdf_files",
    out_dir="path/to/output",        # Optional: defaults to <in_dir>/output
    output_format="json",            # Options: 'json' (default) or 'ascii'
    start_time='YYYY-MM-DDT00:00',   # Optional if not entire file is to be processed
    end_time='YYYY-MM-DDT00:00'
)

processor.run()
```

## Contact

* Jordan Guerra <jordan.guerra@noaa.gov>
* Adam Kubaryk <adam.kubaryk@noaa.gov>

