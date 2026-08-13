import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List
from netCDF4 import Dataset
from cftime import num2date
import numpy as np


class GeoelectricPostprocessor:
    """Post-processing NOAA/SWPC-USGS Geoelectric Field NetCDF model outputs into GeoJSON or ASCII data products."""

    def __init__(
        self,
        in_dir: Union[str, Path],
        out_dir: Optional[Union[str, Path]] = None,
        output_format: str = "json",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ):
        self.in_path = Path(in_dir).resolve()

        if out_dir is None:
            self.out_dir = (self.in_path if self.in_path.is_dir() else self.in_path.parent) / "output"
        else:
            self.out_dir = Path(out_dir).resolve()

        fmt = output_format.lower()
        if fmt in ("json", "geojson"):
            self.output_format = "json"
        elif fmt in ("ascii", "dat"):
            self.output_format = "ascii"
        else:
            raise ValueError(f"Unsupported output format: '{output_format}'. Choose 'json' or 'ascii'.")

        # Safely parse timestamps, handling empty strings ('') as None
        self.start_time = (
            datetime.fromisoformat(start_time.strip())
            if (start_time and str(start_time).strip())
            else None
        )
        self.end_time = (
            datetime.fromisoformat(end_time.strip())
            if (end_time and str(end_time).strip())
            else None
        )

    def _get_input_files(self) -> List[Path]:
        if self.in_path.is_file():
            return [self.in_path]
        elif self.in_path.is_dir():
            files = sorted(self.in_path.glob("*.nc"))
            if not files:
                print(f"Warning: No .nc files found in directory '{self.in_path}'", file=sys.stderr)
            return files
        else:
            raise FileNotFoundError(f"Input path '{self.in_path}' does not exist.")

    def run(self) -> None:
        """Processes all matching NetCDF input files."""
        files = self._get_input_files()
        if not files:
            return

        self.out_dir.mkdir(parents=True, exist_ok=True)

        for filepath in files:
            self._process_file(filepath)

    def _process_file(self, file_path: Path) -> None:
        with Dataset(file_path, "r", format="NETCDF4") as nc:
            tstamp_var = nc.variables["time"]
            units = tstamp_var.UNITS
            calendar = getattr(tstamp_var, "calendar", "standard")

            # Standard netCDF4 conversion to Python datetime objects
            raw_dates = num2date(tstamp_var[:], units=units, calendar=calendar, only_use_cftime_datetimes=False)
            times = np.asarray(raw_dates)

            # Filter indices by time range
            if self.start_time or self.end_time:
                mask = np.ones(len(times), dtype=bool)
                if self.start_time:
                    mask &= (times >= self.start_time)
                if self.end_time:
                    mask &= (times <= self.end_time)
                toi_indices = np.where(mask)[0]
            else:
                toi_indices = np.arange(len(times))

            if len(toi_indices) == 0:
                print(f"No timestamps matched time window for {file_path.name}.")
                return

            toi = times[toi_indices]
            print(f"Processing {len(toi)} record(s) from '{file_path.name}' -> {self.output_format.upper()}...")

            # Spatial grid extraction & lexical sorting
            lons = nc.variables["longitude"][:]
            lats = nc.variables["latitude"][:]
            distance = nc.variables["distance"][:]
            sort_idx = np.lexsort((lats, lons))

            lons = np.ascontiguousarray(lons[sort_idx], dtype=np.float64)
            lats = np.ascontiguousarray(lats[sort_idx], dtype=np.float64)

            Ex = nc.variables["Ex"][:][toi_indices][:, sort_idx]
            Ey = nc.variables["Ey"][:][toi_indices][:, sort_idx]
            emax = nc.variables["emax"][:][toi_indices]
            quality = nc.variables["Quality"][:][toi_indices][:, sort_idx]
            distance = nc.variables["distance"][:][sort_idx]
            nobs = nc.variables["nobs"][:][toi_indices]

            model_type = getattr(nc, "MODEL_TYPE", "unknown")
            cadence = getattr(nc, "CADENCE", "60 seconds")
            ngridpts = str(getattr(nc, "NGRIDPTS", len(lons)))
            
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if self.output_format == "json":
                self._export_json(toi, nobs, model_type, cadence, lons, lats, Ex, Ey, quality, distance)
            else:
                self._export_ascii(
                    toi, nobs, model_type, cadence, ngridpts, emax, times[-1],
                    file_mtime, lons, lats, Ex, Ey, quality, distance
                )

    def _export_json(self, toi, nobs, model_type, cadence, lons, lats, Ex, Ey, quality, distance):
        n_points = len(lons)
        coords = [list(c) for c in zip(lons, lats)]
        dists = [float(d) for d in distance]

        for i, dt in enumerate(toi):
            fname = f"{dt.strftime('%Y%m%dT%H%M%S')}-{nobs[i]}-Efield-{model_type}-0.5x0.5.json"

            ex_row = Ex[i]
            ey_row = Ey[i]
            q_row = quality[i]

            ex_row[np.isnan(ex_row)] = 999999.
            ey_row[np.isnan(ey_row)] = 999999.

            features = [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": coords[j]},
                    "properties": {
                        "Ex": float(ex_row[j]),
                        "Ey": float(ey_row[j]),
                        "quality_flag": float(q_row[j]),
                        "distance_nearest_station": dists[j],
                    },
                }
                for j in range(n_points)
            ]

            payload = {
                "time_tag": dt.isoformat(),
                "cadence": cadence,
                "product_version": model_type,
                "type": "FeatureCollection",
                "features": features,
            }

            out_file = self.out_dir / fname
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, separators=(",", ":"))

    def _export_ascii(self, toi, nobs, model_type, cadence, ngridpts, emax, last_time, file_mtime, lons, lats, Ex, Ey, quality, distance):
        grid_data_static = np.column_stack((lons, lats))
        last_insert_time_str = last_time.strftime("%Y-%m-%d %H:%M:%S")
        gen_time_str = file_mtime.strftime("%Y-%m-%d %H:%M:%S")

        for i, dt in enumerate(toi):
            fname = f"{dt.strftime('%Y%m%dT%H%M%S')}-{nobs[i]}-Efield-{model_type}-0.5x0.5.dat"

            header_lines = [
                f"# {'product_filename':<30}{fname}",
                f"# {'time_tag':<30}{dt.strftime('%Y-%m-%d %H:%M:%S')}",
                f"# {'product_generation_time':<30}{gen_time_str}",
                f"# {'product_version':<30}{model_type}",
                f"# {'cadence':<30}{cadence}",
                f"# {'n_stations':<30}{nobs[i]}",
                f"# {'n_gridpts':<30}{ngridpts}",
                f"# {'last_insert_time':<30}{last_insert_time_str}",
                f"# {'resolution':<30}0.5x0.5 degree",
                f"# {'grid_type':<30}empirical-EMTF output",
                f"# {'maximum_efield':<30}{emax[i]:2.2f}",
                "# lon,lat,Ex,Ey,quality_flag,distance_nearest_station\n",
            ]

            table_data = np.column_stack((
                grid_data_static,
                Ex[i],
                Ey[i],
                quality[i],
                distance
            ))

            out_file = self.out_dir / fname
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("\n".join(header_lines))
                np.savetxt(f, table_data, fmt="%2.2f", delimiter=",")
