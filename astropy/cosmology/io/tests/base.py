# Licensed under a 3-clause BSD style license - see LICENSE.rst

# THIRD PARTY
import pytest

# LOCAL
import astropy.units as u
from astropy.cosmology import Cosmology, Parameter, realizations
from astropy.cosmology.core import _COSMOLOGY_CLASSES
from astropy.cosmology.parameters import available

cosmo_instances = [getattr(realizations, name) for name in available]


##############################################################################


class IOTestMixinBase:
    """
    Tests for a Cosmology[To/From]Format with some ``format``.
    This class will not be directly called by :mod:`pytest` since its name does
    not begin with ``Test``. To activate the contained tests this class must
    be inherited in a subclass. Subclasses must define a :func:`pytest.fixture`
    ``cosmo`` that returns/yields an instance of a |Cosmology|.
    See ``TestCosmologyToFromFormat`` or ``TestCosmology`` for examples.
    """

    @pytest.fixture
    def to_format(self, cosmo):
        """Convert Cosmology instance using ``.to_format()``."""
        return cosmo.to_format

    @pytest.fixture
    def from_format(self, cosmo):
        """Convert yaml to Cosmology using ``Cosmology.from_format()``."""
        return Cosmology.from_format


class ToFromFormatTestBase(IOTestMixinBase):
    """
    Directly test ``to/from_<format>``.
    These are not public API and are discouraged from use, in favor of
    ``Cosmology.to/from_format(..., format="<format>")``, but should be tested
    regardless b/c 3rd party packages might use these in their Cosmology I/O.
    Also, it's cheap to test.

    Subclasses should have an attribute ``functions`` which is a dictionary
    containing two items: ``"to"=<function for to_format>`` and
    ``"from"=<function for from_format>``.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup(self):
        """Setup and teardown for tests."""

        class CosmologyWithKwargs(Cosmology):
            Tcmb0 = Parameter(unit=u.K)

            def __init__(self, Tcmb0=0, name="cosmology with kwargs", meta=None, **kwargs):
                super().__init__(name=name, meta=meta)
                self._Tcmb0 = Tcmb0 << u.K

        yield  # run tests

        # pop CosmologyWithKwargs from registered classes
        # but don't error b/c it can fail in parallel
        _COSMOLOGY_CLASSES.pop(CosmologyWithKwargs.__qualname__, None)

    @pytest.fixture(params=cosmo_instances)
    def cosmo(self, request):
        """Cosmology instance."""
        if isinstance(request.param, str):  # CosmologyWithKwargs
            return _COSMOLOGY_CLASSES[request.param](Tcmb0=3)
        return request.param

    @pytest.fixture
    def to_format(self, cosmo):
        """Convert Cosmology to yaml using function ``self.to_function``."""
        return lambda *args, **kwargs: self.functions["to"](cosmo, *args, **kwargs)

    @pytest.fixture
    def from_format(self):
        """Convert yaml to Cosmology using function ``from_function``."""
        def use_from_format(*args, **kwargs):
            kwargs.pop("format", None)  # specific to Cosmology.from_format
            return self.functions["from"](*args, **kwargs)

        return use_from_format