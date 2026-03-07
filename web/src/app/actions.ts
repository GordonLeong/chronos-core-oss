"use server"

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
    createUniverse,
    updateUniverse,
    addTickerToUniverse,
    runUniverseScan,
} from "@/lib/api";

export async function runCandidates(formData: FormData) {
    const universe_id = Number(formData.get("universe_id"));
    const template_id = Number(formData.get("template_id"));
    if (!Number.isFinite(universe_id) || !Number.isFinite(template_id)) return;
    const result = await runUniverseScan(universe_id, {
        template_id,
        provider: "yahooquery",
        interval: "1d"
    });
    const encoded = encodeURIComponent(JSON.stringify(result));
    revalidatePath("/");
    redirect(`/?universe=${universe_id}&scan=${encoded}`);
}

export async function createUniverseAction(formData: FormData) {
    const name = String(formData.get("name") ?? "").trim();
    const description = String(formData.get("description") ?? "").trim() || null;
    if (!name) return;
    try {
        await createUniverse({ name, description });
    } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create universe";
        redirect(`/?universe_error=${encodeURIComponent(message)}`);
    }
    revalidatePath("/");
    redirect(`/?universe_success=${encodeURIComponent("Universe created")}`)

}

export async function updateUniverseAction(formData: FormData) {
    const universeId = Number(formData.get("universe_id"));
    const name = String(formData.get("name") ?? "").trim() || null;
    const description = String(formData.get("description") ?? "").trim() || null;
    if (!Number.isFinite(universeId)) return;

    //Patch payload is partial, to only include fields that the user is changing
    const payload: {
        name?: string;
        description?: string | null
    } = {};
    if (name) payload.name = name;
    if (formData.has("description")) payload.description = description;
    if (Object.keys(payload).length === 0) return;
    try {
        await updateUniverse(universeId, payload);
        revalidatePath("/");
    } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to update universe";
        redirect(`/?universe_error=${encodeURIComponent(message)}`);
    }
    revalidatePath("/");
    redirect(`/?universe_success=${encodeURIComponent("Universe updated")}`);
}

export async function addTickerAction(formData: FormData) {
    const universeId = Number(formData.get("universe_id"));
    const ticker = String(formData.get("ticker") ?? "").trim();
    if (!Number.isFinite(universeId) || !ticker)
        return;
    try {
        await addTickerToUniverse(universeId, ticker);

    } catch (err) {
        const message = err instanceof Error ? err.message : "failed to add ticker";
        redirect(`/?universe=${universeId}&ticker_error=${encodeURIComponent(message)}`)
    }
    revalidatePath("/");
    redirect(`/?universe=${universeId}&ticker_success=${encodeURIComponent("Ticker added")}`);
}