# FWS NWI Extension Specification

- **Title:** U.S. Fish & Wildlife Service (FWS) National Wetlands Inventory (NWI)
- **Identifier:** <https://raw.githubusercontent.com/stactools-packages/fws-nwi/main/extension/schema.json>
- **Field Name Prefix:** fws_nwi
- **Scope:** Item, Collection
- **Extension [Maturity Classification](https://github.com/radiantearth/stac-spec/tree/master/extensions/README.md#extension-maturity):** Proposal
- **Owner**: @m-mohr

This document explains the U.S. Fish & Wildlife Service (FWS) National Wetlands Inventory (NWI) Extension to the
[SpatioTemporal Asset Catalog](https://github.com/radiantearth/stac-spec) (STAC) specification.
See <https://www.fws.gov/program/national-wetlands-inventory> for details.

- Examples:
  - [Item example](../examples/item-conus.json): Shows the basic usage of the extension in a STAC Item
  - [Collection example](../examples/collection.json): Shows the basic usage of the extension in a STAC Collection
- [JSON Schema](schema.json)

## Item Properties and Collection Summaries

| Field Name         | Type      | Description                                                  |
| ------------------ | --------- | ------------------------------------------------------------ |
| fws_nwi:state      | string    | **REQUIRED**. The applicable US state (long name). One of the [allowed values](#allowed-values) below. |
| fws_nwi:state_code | string    | **REQUIRED**. The applicable US state (short code). One of the [allowed values](#allowed-values) below. |
| fws_nwi:content    | \[string] | **REQUIRED**. The content published in this Item. A set of the following allowed values: `historic_wetlands`, `riparian`, `wetlands` |

### Allowed Values

| `fws_nwi:state_code` | `fws_nwi:state`                |
| -------------------- | ------------------------------ |
| AL                   | Alabama                        |
| AK                   | Alaska                         |
| AZ                   | Arizona                        |
| AR                   | Arkansas                       |
| CA                   | California                     |
| CO                   | Colorado                       |
| CT                   | Connecticut                    |
| DE                   | Delaware                       |
| DC                   | District of Columbia           |
| FL                   | Florida                        |
| GA                   | Georgia                        |
| HI                   | Hawaii                         |
| ID                   | Idaho                          |
| IL                   | Illinois                       |
| IN                   | Indiana                        |
| IA                   | Iowa                           |
| KS                   | Kansas                         |
| KY                   | Kentucky                       |
| LA                   | Louisiana                      |
| ME                   | Maine                          |
| MD                   | Maryland                       |
| MA                   | Massachusetts                  |
| MI                   | Michigan                       |
| MN                   | Minnesota                      |
| MS                   | Mississippi                    |
| MO                   | Missouri                       |
| MT                   | Montana                        |
| NE                   | Nebraska                       |
| NV                   | Nevada                         |
| NH                   | New Hampshire                  |
| NJ                   | New Jersey                     |
| NM                   | New Mexico                     |
| NY                   | New York                       |
| NC                   | North Carolina                 |
| ND                   | North Dakota                   |
| OH                   | Ohio                           |
| OK                   | Oklahoma                       |
| OR                   | Oregon                         |
| PacTrust             | Pacific Trust Islands          |
| PA                   | Pennsylvania                   |
| PRVI                 | Puerto Rico and Virgin Islands |
| RI                   | Rhode Island                   |
| SC                   | South Carolina                 |
| SD                   | South Dakota                   |
| TN                   | Tennessee                      |
| TX                   | Texas                          |
| UT                   | Utah                           |
| VT                   | Vermont                        |
| VA                   | Virginia                       |
| WA                   | Washington                     |
| WV                   | West Virginia                  |
| WI                   | Wisconsin                      |
| WY                   | Wyoming                        |

## Contributing

All contributions are subject to the
[STAC Specification Code of Conduct](https://github.com/radiantearth/stac-spec/blob/master/CODE_OF_CONDUCT.md).
For contributions, please follow the
[STAC specification contributing guide](https://github.com/radiantearth/stac-spec/blob/master/CONTRIBUTING.md) Instructions
for running tests are copied here for convenience.
