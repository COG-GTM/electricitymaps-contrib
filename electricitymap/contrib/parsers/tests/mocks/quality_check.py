"""
Test datapoints for quality.py
Each one is designed to test some part of the validation functions.
"""

from datetime import datetime, timedelta, timezone

dt = datetime.now(timezone.utc)

prod = {
    "biomass": 15.0,
    "coal": 130.0,
    "gas": 890.0,
    "hydro": 500.0,
    "nuclear": 345.7,
    "oil": 0.0,
    "solar": 60.0,
    "wind": 75.0,
    "geothermal": None,
    "unknown": 3.0,
}

c1 = {
    "consumption": 1374.0,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

c2 = {
    "consumption": -1081.0,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

c3 = {
    "consumption": None,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

e1 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": dt,
    "netFlow": 73.0,
    "source": "mysource.com",
}

e2 = {"sortedZoneKeys": "DK->NO", "netFlow": 73.0, "source": "mysource.com"}

e3 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": "At the 3rd beep the time will be......",
    "netFlow": 73.0,
    "source": "mysource.com",
}

future = datetime.now(timezone.utc) + timedelta(minutes=55)

e4 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": future,
    "netFlow": 73.0,
    "source": "mysource.com",
}

# Valid production datapoint.
p1 = {
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

# Production datapoint where the sum of values is negative.
p2 = {
    "zoneKey": "FR",
    "datetime": dt,
    "production": {
        "biomass": 10.0,
        "coal": -200.0,
    },
    "source": "mysource.com",
}

# Production datapoint where total exceeds 500GW (i.e. > 500_000 MW).
p3 = {
    "zoneKey": "FR",
    "datetime": dt,
    "production": {
        "biomass": 10.0,
        "coal": 600_000.0,
    },
    "source": "mysource.com",
}

# Production datapoint missing the required `production` key.
p4 = {
    "zoneKey": "FR",
    "datetime": dt,
    "source": "mysource.com",
}

# Production datapoint where a single mode exceeds 500GW but total stays below.
p5 = {
    "zoneKey": "FR",
    "datetime": dt,
    "production": {
        "biomass": 600_000.0,
        "coal": -200_000.0,
    },
    "source": "mysource.com",
}
