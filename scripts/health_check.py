"""Daily health check: confirm every data source still answers with the fields we expect.

Plan (issue #2):
1. Load endpoints from config/sources.yaml.
2. For one known sample point per source, run a point-in-polygon query
   (geometryType=esriGeometryPoint, spatialRel=esriSpatialRelIntersects, outFields=...).
3. Fail (exit 1) if a source errors, times out, or a required field is missing.
4. GitHub Actions runs this daily and emails on failure.
"""

import sys


def main() -> int:
    raise NotImplementedError("Implement in issue #2")


if __name__ == "__main__":
    sys.exit(main())
