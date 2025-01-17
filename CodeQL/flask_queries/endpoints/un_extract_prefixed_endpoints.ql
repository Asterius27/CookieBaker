import python
import codeql_library.FlaskLogin

from Function f, Keyword kw, string str, API::CallNode cn, Expr decorator
where f = FlaskLogin::getFunctionViews()
	and f.getADecorator() = decorator
	and (decorator.(Call).getFunc().(Attribute).getAttr() = "route"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "get"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "post"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "put"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "delete"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "patch"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "options"
		or decorator.(Call).getFunc().(Attribute).getAttr() = "head")
	and (str = decorator.(Call).getPositionalArg(0).(StringLiteral).getText()
		or (kw = decorator.(Call).getANamedArg().(Keyword)
			and kw.getArg() = "rule"
			and str = kw.getValue().(StringLiteral).getText()))
	and cn = API::moduleImport("flask").getMember("Blueprint").getACall()
	and decorator.(Call).getFunc().(Attribute).getObject() = cn.getReturn().getAValueReachableFromSource().asExpr()
select f, f.getLocation(), FlaskLogin::calculateURLPrefix(cn) + str
