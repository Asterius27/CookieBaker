import python
import semmle.python.ApiGraphs
import semmle.python.frameworks.Flask

module FlaskLogin {
    bindingset[main, suf]
    int sufcalc(string main, string suf) {
        result = main.length() - suf.length()
    }

    predicate formClass(Class cls) {
        exists(cls.getLocation().getFile().getRelativePath())
        and (cls.getABase().toString() = "Form"
            or cls.getABase().toString() = "BaseForm"
            or cls.getABase().toString() = "FlaskForm")
    }

    predicate classWithPasswordField(Class cls) {
        exists(API::Node node | 
            (node = API::moduleImport("wtforms").getMember("PasswordField")
                or node = API::moduleImport("flask_wtf").getMember("PasswordField"))
            and cls.getAStmt().(AssignStmt).getValue().(Call).getFunc() = node.getAValueReachableFromSource().asExpr())
    }

    Class getSignUpFormClass() {
        exists(Class cls, Class supercls |
            if exists(Class superclss | superclss.getName() = cls.getABase().(Name).getId())
            then supercls.getName() = cls.getABase().(Name).getId()
                and (formClass(cls)
                    or formClass(supercls))
                and (classWithPasswordField(cls)
                    or classWithPasswordField(supercls))
                and (cls.getName().toLowerCase().matches("%registration%")
                    or cls.getName().toLowerCase().matches("%register%")
                    or cls.getName().toLowerCase().matches("%createaccount%")
                    or cls.getName().toLowerCase().matches("%signup%")
                    or cls.getName().toLowerCase().matches("%adduser%")
                    or cls.getName().toLowerCase().matches("%useradd%")
                    or cls.getName().toLowerCase().matches("%regform%")
                    or cls.getName().toLowerCase().matches("%newuser%")
                    or cls.getName().toLowerCase().matches("%userform%")
                    or cls.getName().toLowerCase().matches("%usersform%")
                    or cls.getName().toLowerCase().matches("%registform%"))
                and result = cls
            else formClass(cls)
                and classWithPasswordField(cls)
                and (cls.getName().toLowerCase().matches("%registration%")
                    or cls.getName().toLowerCase().matches("%register%")
                    or cls.getName().toLowerCase().matches("%createaccount%")
                    or cls.getName().toLowerCase().matches("%signup%")
                    or cls.getName().toLowerCase().matches("%adduser%")
                    or cls.getName().toLowerCase().matches("%useradd%")
                    or cls.getName().toLowerCase().matches("%regform%")
                    or cls.getName().toLowerCase().matches("%newuser%")
                    or cls.getName().toLowerCase().matches("%userform%")
                    or cls.getName().toLowerCase().matches("%usersform%")
                    or cls.getName().toLowerCase().matches("%registform%"))
                and result = cls)
    }

    string getPasswordFieldName(Class cls) {
        exists(DataFlow::Node node | 
            (node = API::moduleImport("wtforms").getMember("PasswordField").getReturn().getAValueReachableFromSource()
                or node = API::moduleImport("flask_wtf").getMember("PasswordField").getReturn().getAValueReachableFromSource())
            and cls.getBody().contains(node.asCfgNode().getNode())
            and result = node.asExpr().(Name).toString())
    }

    Class getClassViews() {
        exists(Class cls, DataFlow::Node node |
            (node = API::moduleImport("flask").getMember("views").getMember("View").getAValueReachableFromSource()
                or node = API::moduleImport("flask").getMember("views").getMember("MethodView").getAValueReachableFromSource())
            and cls.getABase() = node.asExpr()
            and result = cls)
    }
    
    Function getFunctionViews() {
        exists(Function f |
            (f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "route"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "get"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "post"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "put"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "delete"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "patch"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "options"
                or f.getADecorator().(Call).getFunc().(Attribute).getAttr() = "head")
            and result = f)
    }

    string calculateURLPrefixAux(API::CallNode cn) {
        if exists(API::Node nd |
            nd = Flask::FlaskApp::instance().getMember("register_blueprint")
            and (cn.getReturn().getAValueReachableFromSource().asCfgNode() = nd.getParameter(0).getAValueReachingSink().asCfgNode()
                or cn.getReturn().getAValueReachableFromSource().asCfgNode() = nd.getKeywordParameter("blueprint").getAValueReachingSink().asCfgNode()))
        then exists(API::Node reg_blp | 
            reg_blp = Flask::FlaskApp::instance().getMember("register_blueprint")
            and (cn.getReturn().getAValueReachableFromSource().asCfgNode() = reg_blp.getParameter(0).getAValueReachingSink().asCfgNode()
                or cn.getReturn().getAValueReachableFromSource().asCfgNode() = reg_blp.getKeywordParameter("blueprint").getAValueReachingSink().asCfgNode())
            and (result = cn.getParameter(5).getAValueReachingSink().asExpr().(StringLiteral).getText()
                or result = cn.getKeywordParameter("url_prefix").getAValueReachingSink().asExpr().(StringLiteral).getText()
                or result = reg_blp.getKeywordParameter("url_prefix").getAValueReachingSink().asExpr().(StringLiteral).getText()))
        else if exists(API::Node nd |
            nd = API::moduleImport("flask").getMember("Blueprint").getReturn().getMember("register_blueprint")
            and (cn.getReturn().getAValueReachableFromSource().asCfgNode() = nd.getParameter(0).getAValueReachingSink().asCfgNode()
                or cn.getReturn().getAValueReachableFromSource().asCfgNode() = nd.getKeywordParameter("blueprint").getAValueReachingSink().asCfgNode()))
            then exists(API::Node reg_blp, API::CallNode rec | 
                rec = API::moduleImport("flask").getMember("Blueprint").getACall()
                and reg_blp = rec.getReturn().getMember("register_blueprint")
                and (cn.getReturn().getAValueReachableFromSource().asCfgNode() = reg_blp.getParameter(0).getAValueReachingSink().asCfgNode()
                    or cn.getReturn().getAValueReachableFromSource().asCfgNode() = reg_blp.getKeywordParameter("blueprint").getAValueReachingSink().asCfgNode())
                and (result = calculateURLPrefixAux(rec) + cn.getParameter(5).getAValueReachingSink().asExpr().(StringLiteral).getText()
                    or result = calculateURLPrefixAux(rec) + cn.getKeywordParameter("url_prefix").getAValueReachingSink().asExpr().(StringLiteral).getText()
                    or result = calculateURLPrefixAux(rec) + reg_blp.getKeywordParameter("url_prefix").getAValueReachingSink().asExpr().(StringLiteral).getText()))
            else result = ""
    }

    string calculateURLPrefix(API::CallNode cn) {
        if calculateURLPrefixAux(cn) = ""
        then (result = cn.getParameter(5).getAValueReachingSink().asExpr().(StringLiteral).getText()
            or result = cn.getKeywordParameter("url_prefix").getAValueReachingSink().asExpr().(StringLiteral).getText())
        else result = calculateURLPrefixAux(cn)
    }

    Function findFunctionView(Function f) {
        if f = FlaskLogin::getFunctionViews()
        then result = f
        else exists(Call c |
            c.getFunc().(Name).getId() = f.getName()
            and exists(c.getLocation().getFile().getRelativePath())
            and result = findFunctionView(c.getScope()))
    }

    Function findFunctionViewClass(Function f) {
        if f.isMethod()
        then result = f
        else exists(Call c |
            c.getFunc().(Name).getId() = f.getName()
            and exists(c.getLocation().getFile().getRelativePath())
            and result = findFunctionViewClass(c.getScope()))
    }

    predicate isModelClass(Class cls) {
        if exists(cls.getABase())
        then if (cls.getABase() = API::moduleImport("sqlalchemy").getMember("orm").getMember("DeclarativeBase").getAValueReachableFromSource().asExpr()
                or cls.getABase() = API::moduleImport("flask_sqlalchemy").getMember("SQLAlchemy").getReturn().getMember("Model").getAValueReachableFromSource().asExpr()
                or cls.getABase() = API::moduleImport("flask_login").getMember("UserMixin").getAValueReachableFromSource().asExpr()
                or cls.getABase() = API::moduleImport("flask_appbuilder").getMember("Model").getAValueReachableFromSource().asExpr()
                or cls.getABase() = API::moduleImport("flask_mongoengine").getMember("MongoEngine").getReturn().getMember("Document").getAValueReachableFromSource().asExpr())
            then any()
            else exists(Class supercls |
                supercls.getName() = cls.getABase().(Name).getId()
                and isModelClass(supercls))
        else none()
    }
    
    predicate isModelFunction(Class cls) {
        if exists(cls.getABase())
        then if (cls.getABase() = API::moduleImport("sqlalchemy").getMember("orm").getMember("declarative_base").getReturn().getAValueReachableFromSource().asExpr()
                or cls.getABase() = API::moduleImport("sqlalchemy").getMember("ext").getMember("declarative").getMember("declarative_base").getReturn().getAValueReachableFromSource().asExpr())
            then any()
            else exists(Class supercls |
                supercls.getName() = cls.getABase().(Name).getId()
                and isModelClass(supercls))
        else none()
    }

    Function findTopLevelFunction(Function f) {
        if exists(Call c | c.getFunc().(Name).getId() = f.getName() and exists(c.getLocation().getFile().getRelativePath()))
        then exists(Call c |
            c.getFunc().(Name).getId() = f.getName()
            and exists(c.getLocation().getFile().getRelativePath())
            and result = findTopLevelFunction(c.getScope()))
        else result = f
    }

}
