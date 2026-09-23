import yaml


class _NoAliasDumper(yaml.SafeDumper):
    """Never emit &id001 / *id001 anchors, even if objects are shared."""

    def ignore_aliases(self, data):
        return True


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
            Dumper=_NoAliasDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True
        )
