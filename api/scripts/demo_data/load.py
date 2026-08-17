"""Load the demo biomarker measurement dataset onto one user's record.

Writes test_data/biomarker_measurements.csv through BiomarkerService — the same validated
path POST /biomarker-measurements takes, differing only in skipping the router and Clerk
auth. Unknown slugs reject the whole batch and the rows land in a single transaction. The
subject's sex and date of birth are set too, since reference bands are stratified by both.

Talks to the dev database over the connector in core/db.py, so it needs the ADC login from
the repository README and the Cloud SQL settings in api/.env. Nothing here runs DDL.

    uv run python scripts/demo_data/load.py --clerk-user-id user_2abc... --replace

The user row must already exist — it is provisioned just-in-time on the first authenticated
request, so sign in once before loading. Read the id off GET /me.
"""

import csv
from pathlib import Path
from typing import Annotated

import typer

import subject
from mirai_api.core.db import session_scope, transaction
from mirai_api.core.deps import get_biomarker_service, get_user_service
from mirai_api.core.enums import Sex
from mirai_api.repositories.users import UserRepository
from mirai_api.schemas.biomarkers import BiomarkerMeasurementCreate
from mirai_api.schemas.me import MeUpdate

CSV_PATH = Path(__file__).resolve().parents[2] / "test_data" / "biomarker_measurements.csv"

SUBJECT = MeUpdate(sex=Sex(subject.SEX), date_of_birth=subject.DATE_OF_BIRTH)


def read_measurements() -> list[BiomarkerMeasurementCreate]:
    """Parse the fixture into schema objects, so a malformed row fails before any write."""
    with CSV_PATH.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    # Column names match the schema's fields; blanks are absent values, not empty strings.
    measurements = []
    for row in rows:
        present = {field: value for field, value in row.items() if value != ""}
        measurements.append(BiomarkerMeasurementCreate.model_validate(present))

    return measurements


def main(
    clerk_user_id: Annotated[str, typer.Option(help="Clerk sub, as shown by GET /me.")],
    replace: Annotated[
        bool,
        typer.Option("--replace", help="Delete existing measurements first."),
    ] = False,
) -> None:
    """Load the demo biomarker measurements onto a user's record."""
    measurements = read_measurements()

    # Same boundary a request gets, so --replace is one atomic delete-then-load.
    with session_scope() as session, transaction(session):
        # Resolve the local row; it exists only once the user has authenticated once.
        user = UserRepository(session).get_user(clerk_user_id)
        if user is None:
            print(f"No user row for {clerk_user_id}. Sign in to the app once to provision it.")
            raise typer.Exit(code=1)

        # The stored reference bounds only mean anything against the subject's profile, so
        # report the overwrite — the previous values may have been real.
        previous = f"{user.sex} {user.date_of_birth}"
        get_user_service(session).update_profile(user, SUBJECT)
        print(f"profile set to {SUBJECT.sex} {SUBJECT.date_of_birth}, was {previous}")

        service = get_biomarker_service(session)

        # Reloading over an existing series would stack duplicate points on every date.
        if replace:
            series = service.list_series(user.id).root
            existing = [point.id for points in series.values() for point in points]
            if existing:
                service.delete_measurements(user.id, existing)
            print(f"deleted {len(existing)} existing measurements")

        created = service.create_measurements(user.id, measurements)
        print(f"loaded {len(created)} measurements for {clerk_user_id}")


if __name__ == "__main__":
    typer.run(main)
