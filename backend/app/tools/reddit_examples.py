"""
Examples demonstrating Reddit market validation features.

This file shows how to use the new Reddit scraping and market validation tools
without needing a Reddit API key!

Run examples:
    python -m app.tools.reddit_examples
"""

import asyncio
from app.tools.reddit import (
    search_reddit,
    get_recent_discussions,
    analyze_course_demand,
    compare_course_providers,
    find_trending_skills,
    validate_curriculum_idea,
)


async def example_1_search_reddit():
    """Example 1: Basic Reddit search for discussions."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Search Reddit for AWS certification discussions")
    print("="*80)
    
    results = await search_reddit(
        query="AWS certification worth it",
        limit=5
    )
    
    print(f"\n✅ Found {len(results)} discussions\n")
    
    for i, post in enumerate(results[:3], 1):
        print(f"{i}. {post.get('title', 'No title')}")
        print(f"   📊 {post.get('upvotes', 0)} upvotes | "
              f"💬 {post.get('comments_count', 0)} comments | "
              f"👍 {int(post.get('upvote_ratio', 0) * 100)}% upvoted")
        print(f"   🔗 {post.get('url', 'No URL')}")
        print(f"   📝 {post.get('post_content', '')[:100]}...")
        print()


async def example_2_recent_posts():
    """Example 2: Get recent posts from career subreddits."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Get recent posts from career subreddits (RSS)")
    print("="*80)
    
    recent = await get_recent_discussions(
        subreddits=["cscareerquestions", "learnprogramming"],
        limit_per_subreddit=5
    )
    
    print(f"\n✅ Got {len(recent)} recent posts\n")
    
    for i, post in enumerate(recent[:5], 1):
        print(f"{i}. [{post.get('subreddit')}] {post.get('title')}")
        print(f"   📊 {post.get('upvotes', 0)} upvotes")
        print()


async def example_3_analyze_demand():
    """Example 3: Analyze market demand for a course topic."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Analyze demand for 'Python for Data Science'")
    print("="*80)
    
    result = await analyze_course_demand("Python for Data Science")
    
    print(f"\n📊 DEMAND ANALYSIS: {result['topic']}")
    print(f"   Total discussions found: {result['total_discussions']}")
    print(f"   ✅ Highly accepted threads: {len(result['highly_accepted'])}")
    print(f"   ❌ Low interest threads: {len(result['low_interest'])}")
    print(f"   😐 Neutral threads: {len(result['neutral'])}")
    
    print(f"\n💭 SENTIMENT:")
    sent = result['sentiment']
    print(f"   Average score: {sent['average_score']}")
    print(f"   Positive: {sent['positive_count']} | "
          f"Negative: {sent['negative_count']} | "
          f"Neutral: {sent['neutral_count']}")
    
    print(f"\n📌 RECOMMENDATION: {result['recommendation']}")
    
    if result['highly_accepted']:
        print("\n🔥 TOP ACCEPTED THREADS:")
        for i, post in enumerate(result['highly_accepted'][:3], 1):
            print(f"   {i}. {post.get('title', 'No title')}")
            print(f"      {post.get('upvotes')} upvotes, "
                  f"{int(post.get('upvote_ratio', 0) * 100)}% ratio")


async def example_4_compare_courses():
    """Example 4: Compare different course providers."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Compare Python course providers")
    print("="*80)
    
    result = await compare_course_providers(
        course_options=[
            "DataCamp Python",
            "Coursera IBM Python",
            "Udemy Jose Portilla Python",
        ],
        topic_context="Python for Data Science"
    )
    
    print(f"\n🏆 COURSE COMPARISON RESULTS\n")
    print(f"Top choice: {result['top_choice']}")
    print(f"Least recommended: {result['least_recommended']}")
    
    print(f"\n📊 DETAILED RANKINGS:\n")
    for course, data in result['full_rankings'].items():
        print(f"📚 {course}")
        print(f"   Total upvotes: {data['total_upvotes']}")
        print(f"   Avg upvote ratio: {data['avg_upvote_ratio']}")
        print(f"   Engagement score: {data['total_engagement']}")
        print(f"   Sentiment: {data['sentiment_score']:.2f}")
        print(f"   Positive/Negative: {data['positive_mentions']}/{data['negative_mentions']}")
        print()


async def example_5_trending_skills():
    """Example 5: Find trending skills in an industry."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Find trending skills in cloud computing")
    print("="*80)
    
    result = await find_trending_skills("cloud computing", limit=20)
    
    print(f"\n🔥 TRENDING SKILLS IN: {result['industry']}")
    print(f"   Analyzed {result['total_discussions_analyzed']} discussions\n")
    
    print("Top 10 Skills:")
    for skill in result['trending_skills'][:10]:
        bar = "█" * (skill['mentions'] // 2)
        print(f"   {skill['skill']:20s} {bar} {skill['mentions']} mentions")
    
    if result['certifications_mentioned']:
        print("\n🎓 Top Certifications Mentioned:")
        for cert in result['certifications_mentioned'][:5]:
            print(f"   - {cert['cert']}: {cert['mentions']} mentions")


async def example_6_full_validation():
    """Example 6: Complete curriculum validation (combines everything!)."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Full curriculum validation for AWS Cloud Architecture")
    print("="*80)
    
    result = await validate_curriculum_idea(
        curriculum_topic="AWS Cloud Architecture",
        alternative_courses=[
            "A Cloud Guru AWS",
            "Stephane Maarek Udemy AWS",
            "Linux Academy AWS"
        ]
    )
    
    print("\n" + result['executive_summary'])
    print("\n" + "="*80)


async def example_7_market_validation_workflow():
    """Example 7: Real-world workflow for validating a new curriculum."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Market Validation Workflow")
    print("="*80)
    
    curriculum_topics = [
        "Kubernetes Administrator",
        "Terraform Infrastructure as Code",
        "AWS Solutions Architect"
    ]
    
    print("\n🔍 Validating multiple curriculum ideas...\n")
    
    for topic in curriculum_topics:
        print(f"\n📝 Analyzing: {topic}")
        print("-" * 60)
        
        # Quick demand check
        demand = await analyze_course_demand(topic)
        
        recommendation = demand['recommendation']
        highly_accepted = len(demand['highly_accepted'])
        low_interest = len(demand['low_interest'])
        sentiment = demand['sentiment']['average_score']
        
        # Decision logic
        if recommendation.startswith('HIGHLY RECOMMENDED'):
            status = "✅ INCLUDE"
        elif recommendation.startswith('RECOMMENDED'):
            status = "⚠️  CONSIDER"
        else:
            status = "❌ SKIP"
        
        print(f"   Status: {status}")
        print(f"   Engagement: {highly_accepted} high / {low_interest} low")
        print(f"   Sentiment: {sentiment:.2f}")
        print(f"   Recommendation: {recommendation}")


async def main():
    """Run all examples."""
    print("\n")
    print("🚀 Reddit Market Validation Examples")
    print("=" * 80)
    print("These examples show how to validate curriculum ideas using Reddit")
    print("without needing a Reddit API key!")
    print("=" * 80)
    
    # Run examples
    examples = [
        ("Basic Search", example_1_search_reddit),
        ("Recent Posts (RSS)", example_2_recent_posts),
        ("Demand Analysis", example_3_analyze_demand),
        ("Course Comparison", example_4_compare_courses),
        ("Trending Skills", example_5_trending_skills),
        ("Full Validation", example_6_full_validation),
        ("Validation Workflow", example_7_market_validation_workflow),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
        
        # Wait between examples to respect rate limits
        await asyncio.sleep(2)
    
    print("\n" + "="*80)
    print("✅ All examples completed!")
    print("="*80)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())

