from crmToVoice import models
from crmToVoice.models.fields import LeadFields, PropertyFields, VisitFields
from crmToVoice.models.interpretation import Interpretation
from crmToVoice.models.state import AgentState, Intent, TargetEntity


def test_models_package_reexports_all_public_names():
    assert models.AgentState is AgentState
    assert models.Intent is Intent
    assert models.TargetEntity is TargetEntity
    assert models.LeadFields is LeadFields
    assert models.PropertyFields is PropertyFields
    assert models.VisitFields is VisitFields
    assert models.Interpretation is Interpretation
