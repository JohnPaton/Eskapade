import ROOT
from ROOT import RooFit
from ROOT import RooWorkspace

from eskapade.core.process_services import ProcessService
from .roofit_models import RooFitModel


class RooFitManager(ProcessService):
    """Process service for managing RooFit operations"""

    _persist = True

    def __init__(self):
        """Initialize RooFit manager instance"""

        self._ws = None
        self._models = {}

    @property
    def ws(self):
        """RooFit workspace for Eskapade run"""

        if not self._ws:
            self._ws = RooWorkspace('esws', 'Eskapade workspace')

        # python does not take ownership of the workspace
        ROOT.SetOwnership(self._ws, False)
        return self._ws

    def set_var_vals(self, vals):
        """Set values of workspace variables

        :param list vals: values and errors to set: [(name1, (val1, err1)), (name2, (val2, err2)), ...]
        """

        for var, (val, err) in vals.items():
            self.ws.var(var).setVal(val)
            self.ws.var(var).setError(err)

    def model(self, name, model_cls=None, *args, **kwargs):
        """Get RooFit model

        Return the RooFit model with the specified name.  Create the model if it
        does not yet exist.  Arguments and key-word arguments are passed on to
        the model when it is initialized.

        :param str name: name of the model
        :param model_cls: model class; must inherit from RooFitModel
        """

        # check name
        name = str(name) if name else ''
        if not name:
            raise ValueError('no valid model name specified')

        # create model if it does not exist and class is specified
        if name not in self._models:
            # check if model should be created
            if not model_cls:
                return None

            # create model
            self._models[name] = model_cls(self.ws, name, *args, **kwargs)

            # check model type
            if not isinstance(self._models[name], RooFitModel):
                raise TypeError('specified model is not a RooFitModel')

        return self._models[name]
