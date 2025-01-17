import python
import codeql_library.DjangoSession

from Function f, string str, API::CallNode node, Attribute attr, Name name
where node = DjangoSession::getURLDefinitions().getACall()
    and str = DjangoSession::getEndpoint(node)
    and ((node.asExpr().contains(attr)
            and attr.getName() = f.getName())
        or (node.asExpr().contains(name)
            and name.getId() = f.getName()))
    and exists(f.getLocation().getFile().getRelativePath())
    and not DjangoSession::isPrefixedURLDefinition(node)
select f, f.getLocation(), str
