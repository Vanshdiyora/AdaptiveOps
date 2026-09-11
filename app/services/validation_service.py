from app.agents.validation.confidence import (
    update_confidence,
)


class ValidationService:

    def finalize(
        self,
        validation_result,
    ):

        evaluations = (
            validation_result.prediction_evaluations
        )

        total_predictions = len(
            evaluations
        )

        matched_predictions = sum(
            1
            for evaluation in evaluations
            if evaluation.matched
        )

        contradicted_predictions = sum(
            1
            for evaluation in evaluations
            if (
                not evaluation.matched
                and evaluation.confidence_delta < 0
            )
        )

        updated_confidence = update_confidence(
            original=validation_result.original_confidence,
            matched_predictions=matched_predictions,
            contradicted_predictions=contradicted_predictions,
            total_predictions=total_predictions,
        )

        validation_result.updated_confidence = (
            updated_confidence
        )

        return validation_result