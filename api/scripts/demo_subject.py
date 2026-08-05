"""The subject the demo dataset describes.

Shared by the generator and the loader: the generator resolves every stored reference bound
against this profile, and the loader writes it onto the user row the app resolves bands
against. Declaring it twice would let a regenerated fixture disagree with the loaded profile
silently, since nothing downstream cross-checks them.
"""

from datetime import date

SEX = "male"
DATE_OF_BIRTH = date(1991, 8, 18)
