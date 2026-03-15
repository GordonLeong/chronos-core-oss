"use server"

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
    updateTemplate,
} from "@/lib/api";



export async function updateTemplateAction(formData: FormData) {
    const templateId = Number(formData.get("template_id"));
    const config_json = String(formData.get("config_json") ?? "").trim();

    if (!Number.isFinite(templateId) || !config_json) return;

    try {
        await updateTemplate(templateId, { config_json });
    } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to update template";
        redirect(`/?template_error=${encodeURIComponent(message)}`);
    }
    revalidatePath("/");
    redirect(`/?template_success=${encodeURIComponent("Template updated")}`);
}