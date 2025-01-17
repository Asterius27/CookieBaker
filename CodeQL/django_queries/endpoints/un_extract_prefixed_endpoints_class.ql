import python
import codeql_library.DjangoSession

from Class cls, string str, API::CallNode node, Attribute attr, Name name
where node = DjangoSession::getURLDefinitions().getACall()
    and str = DjangoSession::getEndpoint(node)
    and ((node.asExpr().contains(attr)
            and attr.getName() = cls.getName())
        or (node.asExpr().contains(name)
            and name.getId() = cls.getName()))
    and exists(cls.getLocation().getFile().getRelativePath())
    and DjangoSession::isPrefixedURLDefinition(node)
select cls, cls.getLocation(), DjangoSession::calculateURLPrefix(node) + str
