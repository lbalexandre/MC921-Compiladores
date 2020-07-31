# Practical Aspects of Compiler Construction

The goal of this task is to write a complete compiler for uC (micro C) Language, designed exclusively for this purpose. uC has the essential features of a realistic programming language, but is small and simple enough that it can be implemented in a few thousand lines of code. 

This task will revolve around several programming projects that taken together form a complete working compiler.

## First Project
The first project requires you to implement a scanner, and a parser for the uC language, specified by uC BNF Grammar notebook. Study the specification of uC grammar carefully. To complete this first project, you will use the PLY, a Python version of the lex/yacc toolset with same functionality but with a friendlier interface.

## Second Project
Once syntax trees are built, additional analysis and synthesis can be done by evaluating attributes and executing code fragments on tree nodes. We can also walk through the AST to generate a linear N-address code, delineated through basic blocks, analogously to LLVM IR. We call this intermediate machine code as uCIR. So, in this second project, you will perform semantic checks on your program, and turn the AST into uCIR. uCIR uses Single Static Assignment (SSA), and can promote stack allocated scalars to virtual registers and remove the load and store operations, allowing better optimizations since values propagate directly to their use sites. The main thing that distinguishes SSA from a conventional three-address code is that all assignments in SSA are for distinguished name variables.
