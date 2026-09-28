# Places

The platform's location reference - every country, region and town its join flow
and member search know, spelled the way it holds them - with a latitude and
longitude for each town that can be placed safely. The `signup` behaviour reads
these to ask where a visitor lives and to send the join flow the town's
coordinates.

Made by `ci/make_places.py`; never edited by hand. `index.json` lists the
countries and their regions; each country has its own file. A town with `null`
could not be placed safely: the visitor can still pick it, and the join flow asks
for the location itself.

Published beside the bundle as `/hub-behaviours/places/<edition>/`, immutable. The
bundle's `SIGNUP_PLACES_EDITION` names the edition it reads.

Coordinates: [GeoNames](https://www.geonames.org/), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
