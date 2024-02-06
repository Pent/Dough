from utils.common_utils import user_credits_available
from utils.constants import MLQueryObject
from utils.data_repo.data_repo import DataRepo
from utils.ml_processor.comfy_data_transform import get_file_zip, get_model_workflow_from_query
from utils.ml_processor.constants import CONTROLNET_MODELS, ML_MODEL, ComfyRunnerModel


def check_user_credits(method):
    def wrapper(self, *args, **kwargs):
        if user_credits_available():
            res = method(self, *args, **kwargs)
            return res
        else:
            raise RuntimeError("Insufficient credits. Please recharge")
    
    return wrapper

def check_user_credits_async(method):
    async def wrapper(self, *args, **kwargs):
        if user_credits_available():
            res = await method(self, *args, **kwargs)
            return res
        else:
            raise RuntimeError("Insufficient credits. Please recharge")
    
    return wrapper

# TODO: add data validation (like prompt can't be empty...)
def get_model_params_from_query_obj(model,  query_obj: MLQueryObject):
    data_repo = DataRepo()

    # handling comfy_runner workflows 
    if model.name == ComfyRunnerModel.name:
        workflow_json = get_model_workflow_from_query(model, query_obj)
        file_zip = get_file_zip(query_obj)

        data = {
            "workflow_json": workflow_json,
            "file_list": file_zip
        }

        return data

    input_image, mask = None, None
    if query_obj.image_uuid:
        image = data_repo.get_file_from_uuid(query_obj.image_uuid)
        if image:
            input_image = image.location
            if not input_image.startswith('http'):
                input_image = open(input_image, 'rb')

    if query_obj.mask_uuid:
        mask = data_repo.get_file_from_uuid(query_obj.mask_uuid)
        if mask:
            mask = mask.location
            if not mask.startswith('http'):
                mask = open(mask, 'rb')

    if model == ML_MODEL.img2img_sd_2_1:
        data = {
            "prompt_strength" : query_obj.strength,
            "prompt" : query_obj.prompt,
            "negative_prompt" : query_obj.negative_prompt,
            "width" : query_obj.width,
            "height" : query_obj.height,
            "guidance_scale" : query_obj.guidance_scale,
            "seed" : query_obj.seed,
            "num_inference_steps" : query_obj.num_inference_steps
        }

        if input_image:
            data['image'] = input_image

    elif model == ML_MODEL.real_esrgan_upscale:
        data = {
            "image": input_image,
            "upscale": query_obj.data.get('upscale', 2),
        }
    elif model == ML_MODEL.stylegan_nada:
        data = {
            "input": input_image,
            "output_style": query_obj.prompt
        }
    elif model == ML_MODEL.sdxl:
        data = {
            "prompt" : query_obj.prompt,
            "negative_prompt" : query_obj.negative_prompt,
            "width" : 1024 if query_obj.width == 512 else 1024,    # 768 is the default for sdxl
            "height" : 1024 if query_obj.height == 512 else 1024,
            "prompt_strength": query_obj.strength,
            "mask": mask
        }

        if input_image:
            data['image'] = input_image

    elif model == ML_MODEL.arielreplicate:
        data = {
            "instruction_text" : query_obj.prompt,
            "seed" : query_obj.seed, 
            "cfg_image" : query_obj.data.get("cfg", 1.2), 
            "cfg_text" : query_obj.guidance_scale, 
            "resolution" : 704
        }

        if input_image:
            data['input_image'] = input_image

    elif model  == ML_MODEL.urpm:
        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'strength': query_obj.strength,
            'guidance_scale': min( query_obj.guidance_scale, 1),
            'num_inference_steps': query_obj.num_inference_steps,
            'upscale': 1,
            'seed': query_obj.seed,
        }

        if input_image:
            data['image'] = input_image

    elif model == ML_MODEL.controlnet_1_1_x_realistic_vision_v2_0:
        data = {
            'prompt': query_obj.prompt,
            'ddim_steps': query_obj.num_inference_steps,
            'strength': query_obj.strength,
            'scale': query_obj.guidance_scale,
            'seed': query_obj.seed
        }

        if input_image:
            data['image'] = input_image

    elif model == ML_MODEL.realistic_vision_v5:
        if not (query_obj.guidance_scale >= 3.5 and query_obj.guidance_scale <= 7.0):
            raise ValueError("Guidance scale must be between 3.5 and 7.0")

        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'guidance': query_obj.guidance_scale,
            'width': query_obj.width,
            'height': query_obj.height,
            'steps': query_obj.num_inference_steps,
            'seed': query_obj.seed if query_obj.seed not in [-1, 0] else 0
        }
    elif model == ML_MODEL.deliberate_v3 or model == ML_MODEL.dreamshaper_v7 or model == ML_MODEL.epicrealism_v5:
        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'width': query_obj.width,
            'height': query_obj.height,
            'prompt_strength': query_obj.strength,
            'guidance_scale': query_obj.guidance_scale,
            'num_inference_steps': query_obj.num_inference_steps,
            'safety_checker': False,
            'seed': query_obj.seed
        }

        if query_obj.seed in [-1, 0]:
                del data['seed']

        if input_image:
            data['image'] = input_image
        if mask:
            data['mask'] = mask

    elif model == ML_MODEL.sdxl_controlnet:
        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'num_inference_steps': query_obj.num_inference_steps,
            'condition_scale': query_obj.data.get('condition_scale', 0.5),
        }

        if input_image:
            data['image'] = input_image
    
    elif model == ML_MODEL.sdxl_controlnet_openpose:
        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'num_inference_steps': query_obj.num_inference_steps,
            'guidance_scale': query_obj.guidance_scale,
        }

        if input_image:
            data['image'] = input_image

    elif model == ML_MODEL.realistic_vision_v5_img2img:
        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'image': input_image,
            'steps': query_obj.num_inference_steps,
            'strength': query_obj.strength
        }

        if input_image:
            data['image'] = input_image

    elif model in CONTROLNET_MODELS:
        if model == ML_MODEL.jagilley_controlnet_scribble and query_obj.data.get('canny_image', None):
            input_image = data_repo.get_file_from_uuid(query_obj.data['canny_image']).location
            if not input_image.startswith('http'):
                input_image = open(input_image, 'rb')

        data = {
            'image': input_image,
            'input_image': input_image,
            'prompt': query_obj.prompt,
            'num_samples': "1",
            'image_resolution': str(query_obj.width),
            'ddim_steps': query_obj.num_inference_steps,
            'scale': query_obj.guidance_scale,
            'eta': 0,
            'seed': query_obj.seed,
            'a_prompt': query_obj.data.get('a_prompt', "best quality, extremely detailed"),
            'n_prompt': query_obj.negative_prompt + ", longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality",
            'detect_resolution': query_obj.width,
            'bg_threshold': 0,
            'low_threshold': query_obj.low_threshold,
            'high_threshold': query_obj.high_threshold,
        }

    elif model in [ML_MODEL.clones_lora_training_2]:
        
        if query_obj.adapter_type:
            adapter_condition_image = input_image
        else:
            adapter_condition_image = ""

        lora_urls = ""
        lora_scales = ""
        lora_model_1_url = query_obj.data.get("lora_model_1_url", None)
        lora_model_2_url = query_obj.data.get("lora_model_2_url", None)
        lora_model_3_url = query_obj.data.get("lora_model_3_url", None)
        if lora_model_1_url:
            lora_urls += lora_model_1_url
            lora_scales += "0.5"
        if lora_model_2_url:
            ctn = "" if not len(lora_urls) else " | "
            lora_urls += ctn + lora_model_2_url
            lora_scales += ctn + "0.5"
        if lora_model_3_url:
            ctn = "" if not len(lora_urls) else " | "
            lora_urls += ctn + lora_model_3_url
            lora_scales += ctn + "0.5"

        data = {
            'prompt': query_obj.prompt,
            'negative_prompt': query_obj.negative_prompt,
            'width': query_obj.width,
            'height': query_obj.height,
            'num_outputs': 1,
            'image': input_image,
            'num_inference_steps': query_obj.num_inference_steps,
            'guidance_scale': query_obj.guidance_scale,
            'prompt_strength': query_obj.strength,
            'scheduler': "DPMSolverMultistep",
            'lora_urls': lora_urls,
            'lora_scales': lora_scales,
            'adapter_type': query_obj.adapter_type,
            'adapter_condition_image': adapter_condition_image,
        } 

    else:
        app_settings = data_repo.get_app_settings()
        data = query_obj.to_json()

        # hackish sol: handling custom dreambooth models
        if app_settings.replicate_username in model.name:
            data = {
                "image": input_image,
                "prompt": query_obj.prompt,
                "prompt_strength": query_obj.strength,
                "height": query_obj.height,
                "width": query_obj.width,
                "disable_safety_check": True,
                "negative_prompt": query_obj.negative_prompt,
                "guidance_scale": query_obj.guidance_scale,
                "seed": -1,
                "num_inference_steps": query_obj.num_inference_steps
            }

            if input_image:
                data['control_image'] = input_image

    return data