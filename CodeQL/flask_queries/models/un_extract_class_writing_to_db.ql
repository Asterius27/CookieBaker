import python
import codeql_library.FlaskLogin
import semmle.python.dataflow.new.DataFlow4

from DataFlow::Node commit, API::Node mid, Function f, Class cl
where(commit = API::moduleImport("sqlalchemy").getMember("orm").getMember("sessionmaker").getReturn().getReturn().getMember("commit").getAValueReachableFromSource()
        or commit = API::moduleImport("sqlalchemy").getMember("orm").getMember("create_session").getReturn().getMember("commit").getAValueReachableFromSource()
        or ((mid = API::moduleImport("sqlalchemy").getMember("orm").getMember("scoped_session")
                or mid = API::moduleImport("sqlalchemy").getMember("orm").getMember("contextual_session"))
            and mid.getParameter(0).getAValueReachingSink().asCfgNode() = API::moduleImport("sqlalchemy").getMember("orm").getMember("sessionmaker").getACall().asCfgNode()
            and commit = mid.getReturn().getReturn().getMember("commit").getAValueReachableFromSource())
        or commit = API::moduleImport("flask_sqlalchemy").getMember("SQLAlchemy").getReturn().getAMember().getMember("commit").getAValueReachableFromSource())
    and f = commit.getScope()
    and f.isMethod()
    and cl.getAMethod() = f
select cl, cl.getLocation()
