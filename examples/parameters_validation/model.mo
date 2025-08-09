model ParametersValidation "A dummy model to show how to validate parameters"
	parameter Real positive_number = 1;
	parameter Real negative_number = -1;

	initial algorithm
		assert(positive_number>0, "`positive_number` must be > 0");
		assert(negative_number<0, "`negative_number` must be < 0");
		assert(positive_number-negative_number > 1, "`positive_number - negative_number` must be > 1");

end ParametersValidation;
