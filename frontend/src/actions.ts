'use server'
import * as api from '@/api'
import { AICPProjectCreate } from '@/typings'
export async function createProject(formData: FormData) {
    console.log(formData)
    let projectCreate: AICPProjectCreate = {
        name: formData.get('name') as string,
        description: formData.get('description') as string,
        program_id: formData.get('program_id') as string,
        production_config_id: formData.get('production_config_id') as string,
    }
    let response = await api.createProject(projectCreate)
    return response
}