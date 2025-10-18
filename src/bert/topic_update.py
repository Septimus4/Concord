# topic_update.py
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timezone
from graph.schema import Topic, TopicUpdate, Channel

SIMILARITY_THRESHOLD = 0.8
AMPLIFY_INCREMENT = 0.1
DIMINISH_DECREMENT = 0.05
NEW_TOPIC_INITIAL_SCORE = 0.1


def compute_cosine_similarity(vector_a, vector_b):
    return cosine_similarity([vector_a], [vector_b])[0][0]


def update_channel_topics(channel_topics, new_topics, channel_id):
    initial_scores = {topic.topic_id: topic.topic_score for topic in channel_topics}
    topic_updates = []

    for new_topic in new_topics:
        print(
            f"\nProcessing new topic: {new_topic['name']} with weight {new_topic['weight']:.4f}"
        )
        similarities = {
            idx: compute_cosine_similarity(
                new_topic["embedding"], channel_topic.topic_embedding
            )
            for idx, channel_topic in enumerate(channel_topics)
        }
        print("Similarity scores:", similarities)

        topic_amplified = False
        for idx, similarity in similarities.items():
            if similarity >= SIMILARITY_THRESHOLD:
                channel_topic = channel_topics[idx]
                original_score = channel_topic.topic_score
                channel_topic.topic_score = min(
                    1, channel_topic.topic_score + AMPLIFY_INCREMENT
                )
                delta = channel_topic.topic_score - original_score
                channel_topic.updated_at = datetime.now(timezone.utc)
                channel_topic.save()
                print(
                    f"Amplifying topic '{channel_topic.name}' from {original_score:.4f} to "
                    f"{channel_topic.topic_score:.4f} (delta = {delta:.4f})"
                )

                topic_update = TopicUpdate.create_topic_update(
                    keywords=channel_topic.keywords, score_delta=delta
                )
                topic_update.topic.connect(channel_topic)
                topic_updates.append(topic_update)

                topic_amplified = True

        if not topic_amplified:
            print(
                f"Creating new topic '{new_topic['name']}' with initial score {NEW_TOPIC_INITIAL_SCORE:.4f}"
            )
            topic_node = Topic(
                name=new_topic["name"],
                topic_embedding=new_topic["embedding"],
                topic_score=NEW_TOPIC_INITIAL_SCORE,
                updated_at=datetime.now(timezone.utc),
            ).save()
            topic_node.add_update(
                new_topic.get("keywords", []), NEW_TOPIC_INITIAL_SCORE
            )
            Channel.nodes.get(channel_id=channel_id).associate_with_topic(
                topic_node,
                NEW_TOPIC_INITIAL_SCORE,
                new_topic.get("keywords", []),
                1,
                "New",
            )
            channel_topics.append(topic_node)

    for channel_topic in channel_topics:
        if channel_topic.name not in [nt["name"] for nt in new_topics]:
            original_score = channel_topic.topic_score
            channel_topic.topic_score = max(
                0, channel_topic.topic_score - DIMINISH_DECREMENT
            )
            delta = original_score - channel_topic.topic_score
            channel_topic.updated_at = datetime.now(timezone.utc)
            channel_topic.save()
            print(
                f"Diminishing topic '{channel_topic.name}' from {original_score:.4f} to "
                f"{channel_topic.topic_score:.4f} (delta = -{delta:.4f})"
            )

            if delta != 0:
                topic_update = TopicUpdate.create_topic_update(
                    keywords=channel_topic.keywords, score_delta=-delta
                )
                topic_update.topic.connect(channel_topic)
                topic_updates.append(topic_update)

    print("\nUpdated Channel Topics:")
    print("{:<30} {:<15} {:<15}".format("Topic Name", "Initial Score", "Updated Score"))
    for topic in channel_topics:
        initial_score = initial_scores.get(topic.topic_id, NEW_TOPIC_INITIAL_SCORE)
        print(
            "{:<30} {:<15.4f} {:<15.4f}".format(
                topic.name, initial_score, topic.topic_score
            )
        )

    return topic_updates
