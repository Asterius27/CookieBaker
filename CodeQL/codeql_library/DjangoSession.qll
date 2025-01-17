import python
import semmle.python.ApiGraphs
import semmle.python.dataflow.new.DataFlow3
import semmle.python.dataflow.new.DataFlow2
import semmle.python.dataflow.new.DataFlow4

module DjangoSession {

    class RequestObjectConfiguration extends DataFlow::Configuration {
        RequestObjectConfiguration() { this = "RequestObjectConfiguration" }
    
        override predicate isSource(DataFlow::Node source) {
            (source.asExpr() = DjangoSession::getARequestObjectFromClassViews(1)
                or source.asExpr() = DjangoSession::getARequestObjectFromFunctionViews()
                or source.asExpr() = DjangoSession::getARequestObjectFromClassViewsUsingSelf())
            and exists(source.getLocation().getFile().getRelativePath())
        }
    
        override predicate isSink(DataFlow::Node sink) {
            exists(Attribute atr | 
                atr.getName() = "user"
                and atr.getObject() = sink.asExpr()
                and exists(sink.getLocation().getFile().getRelativePath()))
        }
    }

    Parameter getARequestObjectFromFunctionViews() {
        exists(Function f, AssignStmt asgn, Expr name, Keyword k |
            (name = asgn.getValue().(List).getAnElt().(Call).getPositionalArg(1)
                or name = asgn.getValue().(Tuple).getAnElt().(Call).getPositionalArg(1)
                or ((k = asgn.getValue().(List).getAnElt().(Call).getANamedArg().(Keyword)
                        or k = asgn.getValue().(Tuple).getAnElt().(Call).getANamedArg().(Keyword))
                    and name = k.getValue()
                    and k.getArg() = "view"))
            and asgn.getATarget().toString() = "urlpatterns"
            and (f.getName() = name.(Attribute).getName()
                or f.getName() = name.(Name).getId()
                or f.getName() = name.(Call).getAPositionalArg().(Name).getId()
                or f.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Name).getId()
                or f.getName() = name.(Call).getAPositionalArg().(Attribute).getName()
                or f.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Attribute).getName())
            and exists(name.getLocation().getFile().getRelativePath())
            and result = f.getArg(0))
    }

    bindingset[pos]
    Parameter getARequestObjectFromClassViews(int pos) {
        exists(AssignStmt asgn, Expr name, Keyword k, Class cls | 
            (name = asgn.getValue().(List).getAnElt().(Call).getPositionalArg(1)
                or name = asgn.getValue().(Tuple).getAnElt().(Call).getPositionalArg(1)
                or ((k = asgn.getValue().(List).getAnElt().(Call).getANamedArg().(Keyword)
                        or k = asgn.getValue().(Tuple).getAnElt().(Call).getANamedArg().(Keyword))
                    and name = k.getValue()
                    and k.getArg() = "view"))
            and asgn.getATarget().toString() = "urlpatterns"
            and (cls.getName() = name.(Call).getFunc().(Attribute).getObject().(Name).getId()
                or cls.getName() = name.(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getAPositionalArg().(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getAPositionalArg().(Call).getFunc().(Attribute).getObject().(Name).getId()
                or cls.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Call).getFunc().(Attribute).getObject().(Name).getId())
            and exists(name.getLocation().getFile().getRelativePath())
            and (result = cls.getAMethod().getArg(pos)
                or result = getARequestObjectFromSuperClassOfClassViews(pos, cls)))
    }

    Parameter getARequestObjectFromSuperClassOfClassViews(int pos, Class cls) {
        exists(Class supercls | 
            supercls.getName() = cls.getABase().toString()
            and exists(supercls.getLocation().getFile().getRelativePath())
            and result = supercls.getAMethod().getArg(pos))
    }

    Attribute getARequestObjectFromClassViewsUsingSelf() {
        exists(Parameter param, Attribute attr |
            param = getARequestObjectFromClassViews(0)
            and attr.getName() = "request"
            and attr.getObject().getAFlowNode() = param.getVariable().getAUse().getNode().getAFlowNode()
            and result = attr)
    }

    ControlFlowNode getAUserObject() {
        exists(DataFlow::Node src, DataFlow::Node sink, RequestObjectConfiguration config, Attribute atr |
            config.hasFlow(src, sink)
            and atr.getName() = "user"
            and atr.getObject() = sink.asExpr()
            and exists(atr.getLocation().getFile().getRelativePath())
            and result = atr.getAFlowNode())
    }

    bindingset[attrName]
    Expr getAttrValue(Class cls, string attrName) {
        exists(AssignStmt asgn | 
            asgn = cls.getAStmt()
            and asgn.getATarget().(Name).getId() = attrName
            and result = asgn.getValue())
    }

    class RequestObjectConfig extends DataFlow4::Configuration {
        RequestObjectConfig() { this = "RequestObjectConfig" }
    
        override predicate isSource(DataFlow4::Node source) {
            exists(source.getLocation().getFile().getRelativePath())
        }
    
        override predicate isSink(DataFlow4::Node sink) {
            exists(Attribute atr | 
                atr.getName() = "user"
                and atr.getObject() = sink.asExpr()
                and exists(sink.getLocation().getFile().getRelativePath()))
        }
    }
    
    bindingset[pos]
    Parameter getARequestObjectFromClassViews(int pos, Class cls) {
        exists(Expr name | 
            exists(name.getLocation().getFile().getRelativePath())
            and (result = cls.getAMethod().getArg(pos)
                or result = getARequestObjectFromSuperClassOfClassViews(pos, cls)))
    }
    
    Attribute getARequestObjectFromClassViewsUsingSelf(Class cls) {
        exists(Parameter param, Attribute attr |
            param = getARequestObjectFromClassViews(0, cls)
            and attr.getName() = "request"
            and attr.getObject().getAFlowNode() = param.getVariable().getAUse().getNode().getAFlowNode()
            and result = attr)
    }
    
    Function getDecoratedFunction(ControlFlowNode node) {
        exists(Function f |
            f.getADecorator().getAFlowNode() = node
            and result = f)
        or exists(Function f, ControlFlowNode cfn, Call cl |
            cfn = API::moduleImport("django").getMember("utils").getMember("decorators").getMember("method_decorator").getACall().asCfgNode()
            and f.getADecorator().getAFlowNode() = cfn
            and cfn = cl.getAFlowNode()
            and (cl.getAPositionalArg().getAFlowNode() = node
                or cl.getANamedArg().(Keyword).getValue().getAFlowNode() = node)
            and result = f)
    }
    
    Class getDecoratedClass(ControlFlowNode node) {
        exists(Class c, ControlFlowNode cfn, Call cl |
            cfn = API::moduleImport("django").getMember("utils").getMember("decorators").getMember("method_decorator").getACall().asCfgNode()
            and c.getADecorator().getAFlowNode() = cfn
            and cfn = cl.getAFlowNode()
            and (cl.getAPositionalArg().getAFlowNode() = node
                or cl.getANamedArg().(Keyword).getValue().getAFlowNode() = node)
            and result = c)
    }
    
    Function getArgumentFunction(Expr node) {
        exists(Call c, Expr expr, Function f |
            c.getFunc().(Name) = node.(Name)
            and exists(node.getLocation().getFile().getRelativePath())
            and (c.contains(expr)
                or c.getNamedArg(0).(Keyword).contains(expr))
            and (expr.(Attribute).getName() = f.getName()
                or expr.(Name).getId() = f.getName())
            and result = f)
    }
    
    Class getArgumentClass(Expr node) {
        exists(Call c, Expr expr, Class cls |
            c.getFunc().(Name) = node.(Name)
            and exists(node.getLocation().getFile().getRelativePath())
            and (c.contains(expr)
                or c.getNamedArg(0).(Keyword).contains(expr))
            and (expr.(Attribute).getName() = cls.getName()
                or expr.(Name).getId() = cls.getName())
            and result = cls)
    }

    Class getClassViews() {
        exists(AssignStmt asgn, Expr name, Keyword k, Class cls | 
            (name = asgn.getValue().(List).getAnElt().(Call).getPositionalArg(1)
                or name = asgn.getValue().(Tuple).getAnElt().(Call).getPositionalArg(1)
                or ((k = asgn.getValue().(List).getAnElt().(Call).getANamedArg().(Keyword)
                        or k = asgn.getValue().(Tuple).getAnElt().(Call).getANamedArg().(Keyword))
                    and name = k.getValue()
                    and k.getArg() = "view"))
            and asgn.getATarget().toString() = "urlpatterns"
            and (cls.getName() = name.(Call).getFunc().(Attribute).getObject().(Name).getId()
                or cls.getName() = name.(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getAPositionalArg().(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Call).getFunc().(Attribute).getObject().(Attribute).getName()
                or cls.getName() = name.(Call).getAPositionalArg().(Call).getFunc().(Attribute).getObject().(Name).getId()
                or cls.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Call).getFunc().(Attribute).getObject().(Name).getId())
            and exists(name.getLocation().getFile().getRelativePath())
            and result = cls)
    }
    
    Function getFunctionViews() {
        exists(Function f, AssignStmt asgn, Expr name, Keyword k |
            (name = asgn.getValue().(List).getAnElt().(Call).getPositionalArg(1)
                or name = asgn.getValue().(Tuple).getAnElt().(Call).getPositionalArg(1)
                or ((k = asgn.getValue().(List).getAnElt().(Call).getANamedArg().(Keyword)
                        or k = asgn.getValue().(Tuple).getAnElt().(Call).getANamedArg().(Keyword))
                    and name = k.getValue()
                    and k.getArg() = "view"))
            and asgn.getATarget().toString() = "urlpatterns"
            and (f.getName() = name.(Attribute).getName()
                or f.getName() = name.(Name).getId()
                or f.getName() = name.(Call).getAPositionalArg().(Name).getId()
                or f.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Name).getId()
                or f.getName() = name.(Call).getAPositionalArg().(Attribute).getName()
                or f.getName() = name.(Call).getANamedArg().(Keyword).getValue().(Attribute).getName())
            and exists(name.getLocation().getFile().getRelativePath())
            and result = f)
    }

    API::Node getURLDefinitions() {
        result = API::moduleImport("django").getMember("urls").getMember("path")
        or result = API::moduleImport("django").getMember("urls").getMember("re_path")
        or result = API::moduleImport("django").getMember("conf").getMember("urls").getMember("re_path")
        or result = API::moduleImport("django").getMember("conf").getMember("urls").getMember("url")
    }
    
    string getEndpoint(API::CallNode cn) {
        result = cn.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText()
        or result = cn.getKeywordParameter("route").getAValueReachingSink().asExpr().(StringLiteral).getText()
        or result = cn.getKeywordParameter("regex").getAValueReachingSink().asExpr().(StringLiteral).getText()
    }

    predicate isPrefixedURLDefinition(API::CallNode node) {
        exists(API::CallNode cfn, API::CallNode cn |
            (cfn = API::moduleImport("django").getMember("urls").getMember("include").getACall()
                or cfn = API::moduleImport("django").getMember("conf").getMember("urls").getMember("include").getACall())
            and cn = DjangoSession::getURLDefinitions().getACall()
            and cn.asExpr().contains(cfn.asExpr())
            and exists(string str | 
                (str = cfn.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText().replaceAll(".", "/")
                    or str = cfn.getKeywordParameter("arg").getAValueReachingSink().asExpr().(StringLiteral).getText().replaceAll(".", "/"))
                and node.getLocation().getFile().getRelativePath().matches("%" + str + "%")))
    }

    string calculateURLPrefix(API::CallNode node) {
        if DjangoSession::isPrefixedURLDefinition(node)
        then exists(API::CallNode cfn, API::CallNode cn |
            (cfn = API::moduleImport("django").getMember("urls").getMember("include").getACall()
                or cfn = API::moduleImport("django").getMember("conf").getMember("urls").getMember("include").getACall())
            and cn = DjangoSession::getURLDefinitions().getACall()
            and cn.asExpr().contains(cfn.asExpr())
            and exists(string str | 
                (str = cfn.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText().replaceAll(".", "/")
                    or str = cfn.getKeywordParameter("arg").getAValueReachingSink().asExpr().(StringLiteral).getText().replaceAll(".", "/"))
                and node.getLocation().getFile().getRelativePath().matches("%" + str + "%"))
            and (result = calculateURLPrefix(cn) + cn.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText()
                or result = calculateURLPrefix(cn) + cn.getKeywordParameter("route").getAValueReachingSink().asExpr().(StringLiteral).getText()
                or result = calculateURLPrefix(cn) + cn.getKeywordParameter("regex").getAValueReachingSink().asExpr().(StringLiteral).getText()))
        else result = ""
    }

    Function findFunctionView(Function f) {
        if f = getFunctionViews()
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

    DataFlow::Node getLoginFunctionCall() {
        exists(DataFlow::Node auth | 
            auth = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("authenticate").getAValueReachableFromSource()
            and not auth.asExpr() instanceof ImportMember
            and exists(auth.asCfgNode())
            and exists(auth.getLocation().getFile().getRelativePath())
            and result = auth)
        or exists(DataFlow::Node login |
            login = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("login").getAValueReachableFromSource()
            and not login.asExpr() instanceof ImportMember
            and exists(login.asCfgNode())
            and exists(login.getLocation().getFile().getRelativePath())
            and result = login)
        or exists(DataFlow::Node form |
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("AuthenticationForm").getAValueReachableFromSource()
            and not form.asExpr() instanceof ImportMember
            and exists(form.asCfgNode())
            and exists(form.getLocation().getFile().getRelativePath())
            and result = form)
        or exists(Class cls, DataFlow::Node form, Name name, DataFlow::Node node | 
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("AuthenticationForm").getAValueReachableFromSource()
            and cls.getABase() = form.asExpr()
            and name.getId() = cls.getName()
            and node.asExpr() = name
            and exists(node.asCfgNode())
            and exists(node.getLocation().getFile().getRelativePath())
            and result = node)
    }

    Class getUserModels() {
        exists(Class cls |
            ((cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
                and (cls.getName().toLowerCase().matches("%user")
                    or cls.getName().toLowerCase().matches("user%")
                    or cls.getName().toLowerCase().matches("%users")
                    or cls.getName().toLowerCase().matches("users%")
                    or cls.getClassObject().hasAttribute("password")
                    or cls.getClassObject().hasAttribute("passwd")
                    or cls.getClassObject().hasAttribute("pwd")))
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("AbstractUser").getAValueReachableFromSource().asExpr()
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("base_user").getMember("AbstractBaseUser").getAValueReachableFromSource().asExpr()
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().asExpr())
            and exists(cls.getLocation().getFile().getRelativePath())
            and result = cls)
    }

    DataFlow::Node getSignUpFormCall() {
        exists(DataFlow::Node form |
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("UserCreationForm").getAValueReachableFromSource()
            and not form.asExpr() instanceof ImportMember
            and exists(form.asCfgNode())
            and exists(form.getLocation().getFile().getRelativePath())
            and result = form)
        or exists(Class cls, DataFlow::Node form, Name name, DataFlow::Node node | 
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("UserCreationForm").getAValueReachableFromSource()
            and cls.getABase() = form.asExpr()
            and name.getId() = cls.getName()
            and node.asExpr() = name
            and exists(node.asCfgNode())
            and exists(node.getLocation().getFile().getRelativePath())
            and result = node)
        or exists(DataFlow::Node form |
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("BaseUserCreationForm").getAValueReachableFromSource()
            and not form.asExpr() instanceof ImportMember
            and exists(form.asCfgNode())
            and exists(form.getLocation().getFile().getRelativePath())
            and result = form)
        or exists(Class cls, DataFlow::Node form, Name name, DataFlow::Node node | 
            form = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("forms").getMember("BaseUserCreationForm").getAValueReachableFromSource()
            and cls.getABase() = form.asExpr()
            and name.getId() = cls.getName()
            and node.asExpr() = name
            and exists(node.asCfgNode())
            and exists(node.getLocation().getFile().getRelativePath())
            and result = node)
        or exists(Class cls, AssignStmt asgn, Class userModel, Name name, DataFlow::Node node, Class meta, DataFlow::Node form, Name nm |
            form = API::moduleImport("django").getMember("forms").getMember("ModelForm").getAValueReachableFromSource()
            and cls.getABase() = form.asExpr()
            and meta = cls.getAStmt().(ClassDef).getDefinedClass()
            and meta.getName() = "Meta"
            and asgn = meta.getAStmt().(AssignStmt)
            and asgn.getATarget().(Name).getId() = "model"
            and asgn.getValue() = name
            and ((name.getId() = userModel.getName()
                    and userModel = getUserModels())
                or name = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().asExpr())
            and nm.getId() = cls.getName()
            and node.asExpr() = nm
            and exists(node.asCfgNode())
            and exists(node.getLocation().getFile().getRelativePath())
            and result = node)
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
