// @ts-nocheck
// Nuxt auto-imports at runtime; import here for TS/IDE type awareness
// Nuxt auto-imports useRuntimeConfig, useState, ref, and $fetch at runtime.

export function useTopics() {
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase as string;

    const error = useState('error', () => ref(''));
    const loading = useState('loading', () => ref(false));
    const query = useState('query', () => ref(''));

    const trending = useState<string[]>('trending', () => ref([]) as any);
    const searchOptions = useState<string[]>('searchOptions', () => ref([]) as any);
    const selectedTopic = useState<string | null>('selectedTopic', () => ref(null) as any);
    const topChannels = useState<{ topic: string; mentions: number }[]>('topChannels', () => ref([]) as any);

    const fetchTrending = async () => {
        try {
            const res = await $fetch(`${apiBase}/trending/topics`, {
                query: { time_window: '24h', topic_limit: 10, channel_limit: 5 },
            });
            const topics = (res as any)?.topics ?? [];
            trending.value = topics.map((t: any) => t.topic);
            if (!selectedTopic.value && trending.value.length) {
                selectedTopic.value = trending.value[0];
            }
        } catch (e: any) {
            error.value = e?.message || 'Failed to fetch trending topics';
        }
    };

        const getChannelTopics = async (platformId: string, channelId: string) => {
            try {
                const res = await $fetch(`${apiBase}/channels/${platformId}/${channelId}/topics`);
                return (res as any)?.topics ?? [];
            } catch (e: any) {
                error.value = e?.message || 'Failed to fetch channel topics';
                return [];
            }
        };

        const getRelatedChannels = async (platformId: string, channelId: string, maxChannels = 5) => {
            try {
                const res = await $fetch(`${apiBase}/channels/${platformId}/${channelId}/related`, {
                    query: { max_channels: maxChannels },
                });
                return (res as any)?.related_channels ?? [];
            } catch (e: any) {
                error.value = e?.message || 'Failed to fetch related channels';
                return [];
            }
        };

    const fetchTopChannelsForTopic = async (topic: string) => {
        // For MVP, approximate "top channels for topic" by querying related channels of
        // a channel that recently mentioned this topic. As we don't have a direct topic->channels
        // endpoint, we leave this as a placeholder using trending result structure if available.
        // If backend adds /topics/{topic}/channels, wire it here.
        try {
            // Find matching topic entry from the last trending fetch
            const res = await $fetch(`${apiBase}/trending/topics`, {
                query: { time_window: '24h', topic_limit: 20, channel_limit: 10 },
            });
            const topics = (res as any)?.topics ?? [];
            const entry = topics.find((t: any) => t.topic?.toLowerCase() === topic.toLowerCase());
            const channels = (entry?.channels ?? []).map((c: any) => ({ topic: c.channel_id, mentions: Math.round(c.similarity_score || 0) }));
            topChannels.value = channels;
        } catch (e: any) {
            error.value = e?.message || 'Failed to fetch channels for topic';
            topChannels.value = [];
        }
    };

    const selectTopic = async (topic: string) => {
        selectedTopic.value = topic;
        await fetchTopChannelsForTopic(topic);
    };

    const submitQuery = async () => {
        loading.value = true;
        error.value = '';
        try {
            // For MVP, just filter trending topics locally by the query string
            if (!trending.value.length) {
                await fetchTrending();
            }
            const q = (query.value || '').toLowerCase().trim();
            searchOptions.value = trending.value.filter((t: string) => t.toLowerCase().includes(q));
            if (searchOptions.value.length) {
                await selectTopic(searchOptions.value[0]);
            }
            if (searchOptions.value.length === 0) {
                error.value = 'No relevant topics are discussed on this server';
            }
        } catch (e: any) {
            error.value = e?.message || 'Search failed';
        } finally {
            loading.value = false;
        }
    };

    // Load trending on first use
    if (!trending.value.length) {
        fetchTrending();
    }

    return {
        loading,
        error,
        query,
        trending,
        selectedTopic,
        topChannels,
        searchOptions,
        selectTopic,
        submitQuery,
            getChannelTopics,
            getRelatedChannels,
    };
}