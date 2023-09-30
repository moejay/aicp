import * as api from "@/api"

export async function GET() {
    let response = (await api.listPrograms())
    return Response.json(response)
}