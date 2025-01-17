import python
import codeql_library.DjangoSession

Function getSignUpFunctionView() {
    result = DjangoSession::getSignUpFormCall().getScope()
}

from Function f
where f = getSignUpFunctionView()
select f, f.getLocation()
