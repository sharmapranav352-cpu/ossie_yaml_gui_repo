import yaml


class OssieGenerator:

    @staticmethod
    def generate(
        model_name,
        description,
        datasets,
        relationships,
        metrics
    ):

        payload = {

            "version": "0.1.1",

            "semantic_model": [

                {

                    "name":
                    model_name,

                    "description":
                    description,

                    "datasets":
                    datasets,

                    "relationships":
                    relationships,

                    "metrics":
                    metrics
                }
            ]
        }

        return yaml.dump(
            payload,
            sort_keys=False,
            default_flow_style=False
        )