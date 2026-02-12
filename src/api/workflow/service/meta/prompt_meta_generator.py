#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Dict, List, Any
from common.conf_serving import getRecipeDir, getRecipeFile
from jinja2 import Environment, meta, StrictUndefined
from ast import literal_eval
import json
import time
import os


class PromptMetaGenerator:
    def __init__(self, logger):
        self._logger = logger
        self._jinja_env = Environment(undefined=StrictUndefined)

    def _extract_required_variables(self, prompt_template: str) -> List[str]:
        parsed_content = self._jinja_env.parse(prompt_template)
        return sorted(meta.find_undeclared_variables(parsed_content))

    def _validate(self, required_vars, prompt_context: Dict[str, Any]) -> List[str]:
        missing_vars = [var for var in required_vars if var not in prompt_context]
        return missing_vars

    def _render(self, template: str, context: Dict[str, Any]) -> str:
        self._template = self._jinja_env.from_string(template)
        return self._template.render(context)

    def _get_workflow_format(self):
        dirpath = getRecipeDir()
        filename = getRecipeFile()
        dag_info = {}

        try:
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r', encoding='utf-8') as fd:
                dag_info = json.load(fd)
        except Exception as e:
            self._logger.error(e)
        return str(dag_info)

    def _get_nodes_id_map(self):
        time_key = format(int(time.time() * 100000), "X")
        nodes_id_map = {
            "INPUT_NODE": f"INPUT_{time_key}",
            "PROMPT_NODE": f"PROMPT_{time_key}",
            "GENERATE_NODE": f"GENERATE_{time_key}",
            "OUTPUT_NODE": f"OUTPUT_{time_key}"
        }
        return nodes_id_map

    def _extract_prompt_params(self, params):
        prompt_info = params.get('prompt_info')
        params_info = prompt_info.get('params_info')
        prompt_templates_params = params_info.get('prompt_templates')
        prompt_templates = [{"refer_type": "direct", "key": params.get("key"), "value": params.get("value")}
                            for params in prompt_templates_params]
        prompt_context_params = params_info.get('prompt_context')
        prompt_context = [{"refer_type": "direct", "key": params.get("key"), "value": params.get("value")}
                          for params in prompt_context_params]
        prompt_info = []
        prompt_info.append({
            "refer_type": "direct",
            "key": "prompt_templates",
            "values": prompt_templates
        })
        prompt_info.append({
            "refer_type": "indirect",
            "key": "prompt_context",
            "values": prompt_context
        })
        return prompt_info

    def _extract_model_asset(self, params):
        model_info = params.get('model_info', {})
        asset_param_info = model_info.get('asset_info', {})
        asset_info = [{"refer_type": "direct", "key": key, "value": value}
                      for key, value in asset_param_info.items()]
        return asset_info

    def _extract_model_params(self, params, prompt_node_id):
        model_info = params.get('model_info', {})
        model_param_info = model_info.get('params_info', {})
        model_info = [{"refer_type": "direct", "key": key, "value": value}
                      for key, value in model_param_info.items()]
        model_info.append({
            "refer_type": "indirect",
            "key": "prompt",
            "value": f"{prompt_node_id}.generate_prompt.prompt"
        })
        return model_info

    def _get_workflow_template(self, nodes_id_map):
        str_wf_meta_template = self._get_workflow_format()
        req_variables = self._extract_required_variables(str_wf_meta_template)
        self._logger.debug(f" - req_variables: {req_variables}")

        missing_vars = self._validate(req_variables, nodes_id_map)
        if missing_vars:
            self._logger.warning(f"Missing variables: {missing_vars}")
            raise ValueError(f"Required variables not provided: {missing_vars}")

        str_wf_meta_template = self._render(str_wf_meta_template, nodes_id_map)
        wf_meta_template = literal_eval(str_wf_meta_template)
        return wf_meta_template

    def _find_edge_info(self, wf_meta_template, target_node_id):
        wf_edges = wf_meta_template.get('edges')
        for wf_edge_map in wf_edges:
            tar_service_id = wf_edge_map.get("target")
            if tar_service_id.find(target_node_id) >= 0:
                return wf_edge_map


    def _set_prompt_param_info(self, prompt_id, wf_meta_template, prompt_info):
        edge_map = self._find_edge_info(wf_meta_template, prompt_id)
        edge_map['param_info'] = prompt_info

    def _set_model_asset_info(self, generate_node_id, wf_meta_template, model_asset_info):
        edge_map = self._find_edge_info(wf_meta_template, generate_node_id)
        edge_map['asset_info'] = model_asset_info

    def _set_model_param_info(self, generate_node_id, wf_meta_template, model_param_info):
        edge_map = self._find_edge_info(wf_meta_template, generate_node_id)
        edge_map['param_info'] = model_param_info

    def gen_prompt_meta_data(self, params):
        self._logger.info(f"# Generate prompt tester meta")
        nodes_id_map = self._get_nodes_id_map()
        prompt_node_id = nodes_id_map.get("PROMPT_NODE")
        generate_node_id = nodes_id_map.get("GENERATE_NODE")
        wf_meta_template = self._get_workflow_template(nodes_id_map)
        prompt_param_info = self._extract_prompt_params(params)
        model_asset_info = self._extract_model_asset(params)
        model_param_info = self._extract_model_params(params, prompt_node_id)
        # print("# PARAMS")
        # print(f"{model_param_info}")

        self._set_prompt_param_info(prompt_node_id, wf_meta_template, prompt_param_info)
        self._set_model_asset_info(generate_node_id, wf_meta_template, model_asset_info)
        self._set_model_param_info(generate_node_id, wf_meta_template, model_param_info)
        return wf_meta_template