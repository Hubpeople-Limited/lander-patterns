# Places

The platform's location reference - every country, region and town its join flow
and member search know, spelled the way it holds them - with a latitude and
longitude for each town that can be placed safely. The `signup` behaviour reads
these to ask where a visitor lives and to send the join flow the town's
coordinates.

Made by `ci/make_places.py`; never edited by hand. `index.json` lists the
countries; each country has its own file. A town with `null` could not be placed
safely: the visitor can still pick it, and the join flow asks for the location
itself.

Two kinds of country. Most are asked in two steps, country then town: their file
and their index row carry `"levels": 2`, the index lists no regions for them, and
the file keeps every town under its region (`""` where the platform records none)
with `order`, each town's region in the platform's own order, so the card can list
the whole country at once. The rest are asked country, region, town: the index
lists their regions, and their towns are biggest first.

Published beside the bundle as `/hub-behaviours/places/<edition>/`, immutable. The
bundle's `SIGNUP_PLACES_EDITION` names the edition it reads.

A town's coordinates are the platform's own wherever its reference places the
town, so a visitor is joined in the town they picked. For the countries asked
region by region, the region sizes, and the coordinates of a town the reference
does not place, come from [GeoNames](https://www.geonames.org/), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Each file's `source`
says where its coordinates come from.
