import python
import codeql_library.DjangoSession

from string str, API::CallNode node
where node = DjangoSession::getURLDefinitions().getACall()
    and str = DjangoSession::getEndpoint(node)
    and not exists(API::CallNode cfn |
        cfn = API::moduleImport("django").getMember("urls").getMember("include").getACall()
        and node.asExpr().contains(cfn.asExpr()))
select node, node.getLocation(), DjangoSession::calculateURLPrefix(node) + str
