import python
import codeql_library.DjangoSession

Function getLoginFunctionView() {
    result = DjangoSession::getLoginFunctionCall().getScope()
}

from Function f
where f = getLoginFunctionView()
select f, f.getLocation()
