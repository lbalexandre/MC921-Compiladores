# Practical Aspects of Compiler Construction

The goal of this task is to write a complete compiler for uC (micro C) Language, designed exclusively for this purpose. uC has the essential features of a realistic programming language, but is small and simple enough that it can be implemented in a few thousand lines of code. We chose the Python programming language for this task because it has clear and direct syntax and allows for rapid prototyping. In addition, we will have at our disposal a wonderful combination of tools and code in Python that make compilers so cool.

C is not a “very high level” language, nor a “big” one, and is not specialized to any particular area of application.
But its absence of restrictions and its generality make it more convenient and effective for many tasks than supposedly more powerful languages."
-- Kernighan and Ritchie
While you don’t need to be a Python wizard to complete the task, you should feel comfortable working with the language, and in particular should know how to program with classes. If you’d like a Python refresher, there are a bunch of useful links on the website to help you get up to speed. I hope that the use of Python in this task doesn’t deter you from taking it.

This task will revolve around several programming projects that taken together form a complete working compiler. You will learn how to put into practice the techniques presented in the theoretical part of this course and will study most of the details involved in the implementation of a "real" compiler.

##First Project
The first project requires you to implement a scanner, and a parser for the uC language, specified by uC BNF Grammar notebook. Study the specification of uC grammar carefully. To complete this first project, you will use the PLY, a Python version of the lex/yacc toolset with same functionality but with a friendlier interface. Details about this project are in the First Project notebook.

## Second Project
Once syntax trees are built, additional analysis and synthesis can be done by evaluating attributes and executing code fragments on tree nodes. We can also walk through the AST to generate a linear N-address code, delineated through basic blocks, analogously to LLVM IR. We call this intermediate machine code as uCIR. So, in this second project, you will perform semantic checks on your program, and turn the AST into uCIR. uCIR uses Single Static Assignment (SSA), and can promote stack allocated scalars to virtual registers and remove the load and store operations, allowing better optimizations since values propagate directly to their use sites. The main thing that distinguishes SSA from a conventional three-address code is that all assignments in SSA are for distinguished name variables. Details about this project are in the Second Project notebook.
