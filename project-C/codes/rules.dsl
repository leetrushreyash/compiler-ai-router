# Custom Compiler Smell DSL
# Write rules using standard logical operators and extracted metrics.

RULE GodClass = FUNC_LOC > 200 AND METHOD_COUNT > 10
RULE ComplexLogic = CYCLO_COMPLEXITY > 15
RULE DeepNesting = MAX_NEST_DEPTH > 5
RULE HighCoupling = EXTERNAL_REF_COUNT > 20
RULE TooManyParameters = PARAM_COUNT > 6
RULE SpagettiCode = CYCLO_COMPLEXITY > 25 AND MAX_NEST_DEPTH > 6 AND LOOP_COUNT > 5
