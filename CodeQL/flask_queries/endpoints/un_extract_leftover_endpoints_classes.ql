import python
import codeql_library.FlaskLogin

from API::Node url_rule, string str, Class cls
where cls = FlaskLogin::getClassViews()
    and (not url_rule = Flask::FlaskApp::instance().getMember("add_url_rule")
        and not url_rule = API::moduleImport("flask").getMember("Blueprint").getACall().getReturn().getMember("add_url_rule"))
    and (str = url_rule.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText()
        or str = url_rule.getKeywordParameter("rule").getAValueReachingSink().asExpr().(StringLiteral).getText())
    and (url_rule.getKeywordParameter("view_func").getAValueReachingSink().asExpr().(Call).getFunc().(Attribute).getObject().(Name).getId() = cls.getName()
        or url_rule.getParameter(2).getAValueReachingSink().asExpr().(Call).getFunc().(Attribute).getObject().(Name).getId() = cls.getName())
select cls, cls.getLocation(), str
