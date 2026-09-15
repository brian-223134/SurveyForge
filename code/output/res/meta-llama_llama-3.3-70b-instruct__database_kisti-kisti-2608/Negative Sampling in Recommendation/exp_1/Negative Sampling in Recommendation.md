# Comprehensive Survey of Negative Sampling in Recommendation Systems

## 1 Introduction

Negative sampling is a crucial technique in recommendation systems, aiming to improve the accuracy and efficiency of recommendations by selectively sampling negative instances. The primary goal of negative sampling is to identify a subset of negative instances from a large pool of candidates, which can effectively represent the negative class and facilitate the training of recommendation models [1]. In the context of recommendation systems, negative sampling is essential for handling large item sets and improving model performance, as it enables the model to differentiate between relevant and irrelevant items [2].

The concept of negative sampling has undergone significant evolution over time, with various methods being proposed to address the challenges associated with it. Early approaches focused on random sampling, which involves selecting negative instances randomly from the pool of candidates [3]. However, random sampling can be inefficient and may not provide a representative sample of negative instances. To address this limitation, more sophisticated methods have been proposed, such as popularity-based sampling, which selects negative instances based on their popularity [4].

Recent advances in negative sampling have focused on developing more efficient and effective methods, such as adversarial sampling and reinforcement learning-based sampling [5]. These methods have shown promising results in improving the accuracy and efficiency of recommendation systems. Furthermore, the integration of negative sampling with other techniques, such as deep learning and graph-based methods, has also been explored [6].

Despite the advancements in negative sampling, there are still several challenges and limitations associated with it. One of the major challenges is the selection of informative negative instances, which can effectively represent the negative class [7]. Another challenge is the mitigation of bias in negative sampling, which can occur due to the imbalance between positive and negative instances [8].

To address these challenges, various strategies have been proposed, such as hard negative mining and negative sampling with memory [9]. These strategies aim to select informative negative instances and mitigate bias in negative sampling. Additionally, the use of techniques such as importance sampling and weighting has also been explored to improve the efficiency and effectiveness of negative sampling [10].

In conclusion, negative sampling is a crucial technique in recommendation systems, and its effectiveness has a significant impact on the accuracy and efficiency of recommendations. The evolution of negative sampling has led to the development of various methods, each with its strengths and limitations. To further improve the performance of recommendation systems, it is essential to continue exploring new strategies and techniques for negative sampling, such as the integration with other methods and the mitigation of bias [11]. By doing so, we can develop more efficient and effective recommendation systems that can provide personalized recommendations to users. Future directions in negative sampling include the exploration of new methods and techniques, such as the use of graph-based methods and deep learning architectures [12]. Additionally, the development of more efficient and effective algorithms for negative sampling is also an important area of research [13].

## 2 Fundamentals of Recommendation Systems

### 2.1 Introduction to Recommendation Systems

Recommendation systems have become an integral part of modern online services, aiming to provide users with personalized content or product suggestions based on their past interactions, preferences, and behaviors [4]. To achieve this, recommendation systems rely on various techniques, including collaborative filtering, content-based filtering, and hybrid approaches. 

Collaborative filtering is a widely used approach in recommendation systems, which leverages the collective behavior of users to generate personalized recommendations [2]. This approach can be further divided into user-based and item-based collaborative filtering, each with its strengths and weaknesses [14]. 

Content-based filtering, on the other hand, recommends items to a user based on the features or attributes of the items themselves [8]. This approach is often used in combination with collaborative filtering to create a hybrid recommendation system [5]. 

One of the key challenges in building effective recommendation systems is the issue of negative sampling [15]. Negative sampling refers to the process of selecting a subset of negative examples from a large pool of potential negative examples [16]. The quality of the negative samples can significantly impact the performance of the recommendation system, and various techniques have been proposed to improve the selection of negative samples [17].

Recent advances in deep learning have also been applied to recommendation systems, with techniques such as neural collaborative filtering and deep matrix factorization showing promising results [18]. These approaches can learn complex patterns and relationships in user behavior and item features, providing more accurate recommendations [19].

Despite the advancements in recommendation systems, there are still several challenges and limitations that need to be addressed. One of the major challenges is the cold start problem, which refers to the difficulty of recommending items to new users or items with limited interaction history. Another challenge is the issue of scalability, as recommendation systems need to handle large volumes of user interaction data and provide recommendations in real-time.

To address these challenges, various techniques have been proposed, including the use of side information, such as user demographics and item attributes [20], and the application of transfer learning and meta-learning [7]. Additionally, the use of negative sampling techniques, such as hard negative sampling and adversarial sampling, can help improve the performance of recommendation systems [21].

In conclusion, recommendation systems are a crucial component of modern online services, and their effectiveness has a significant impact on user experience and business success. By leveraging various techniques, including collaborative filtering, content-based filtering, and hybrid approaches, recommendation systems can provide personalized and accurate recommendations to users. However, there are still several challenges and limitations that need to be addressed, and ongoing research is focused on developing new techniques and improving the performance of existing ones [11].

### 2.2 Collaborative Filtering Techniques

Collaborative filtering (CF) is a fundamental approach in recommendation systems, leveraging the collective behavior of users to generate personalized recommendations [22]. As discussed earlier, recommendation systems rely on various techniques, including collaborative filtering, content-based filtering, and hybrid approaches, to address the complexities of user behavior and item relationships. CF techniques can be broadly categorized into two main approaches: user-based and item-based collaborative filtering. User-based CF involves finding similar users to the active user and recommending items that are liked by these similar users [23]. On the other hand, item-based CF involves finding similar items to the ones that the active user has liked and recommending these similar items [24].

One of the key challenges in CF is the issue of data sparsity, where the user-item interaction matrix is sparse, making it difficult to find similar users or items [25]. To address this issue, various techniques such as matrix factorization and deep learning-based methods have been proposed [26]. Matrix factorization techniques, such as Singular Value Decomposition (SVD) and Non-negative Matrix Factorization (NMF), reduce the dimensionality of the user-item interaction matrix and capture the latent factors that govern user behavior [27]. Deep learning-based methods, on the other hand, learn complex patterns in user behavior using neural networks [28]. These techniques have shown great promise in enhancing the accuracy and diversity of recommendations, and are often used in combination with content-based filtering and hybrid approaches to create more effective recommendation systems.

Another important aspect of CF is the concept of neighborhood-based methods, which involve finding similar users or items based on their proximity in the latent space [29]. These methods can be further divided into two categories: memory-based and model-based methods. Memory-based methods involve storing the user-item interaction matrix in memory and computing similarities between users or items at runtime [30]. Model-based methods, on the other hand, involve training a model on the user-item interaction matrix and using the trained model to make recommendations [31]. Recent advances in deep learning have also been applied to CF, with techniques such as neural collaborative filtering and deep matrix factorization showing promising results [18].

In recent years, there has been a growing interest in developing CF techniques that can handle sequential user behavior, such as session-based recommendation [32]. These techniques involve modeling the sequential patterns in user behavior and using this information to make recommendations. Another important area of research is the development of CF techniques that can handle cold-start problems, where new users or items are introduced, and there is limited interaction data available [33]. The use of meta-learning and transfer learning has shown great promise in improving the performance of CF systems, especially in cold-start scenarios [34]. These techniques involve learning to learn from few examples and adapting to new users or items with limited interaction data.

Despite the many advances in CF techniques, there are still several challenges that need to be addressed, such as the issue of popularity bias, where popular items are over-recommended, and the issue of diversity, where the recommended items are not diverse enough [35]. To address these challenges, various techniques such as re-ranking and regularization have been proposed [36]. The use of multi-task learning and multi-objective optimization has also been proposed to improve the performance of CF systems [37]. These techniques involve optimizing multiple objectives simultaneously, such as accuracy and diversity, to provide more effective recommendations. By understanding the strengths and limitations of these techniques and addressing the challenges that they pose, we can develop more effective CF systems that can provide personalized recommendations to users [38]. 

As we move forward to explore more advanced techniques, such as those discussed in content-based filtering and hybrid approaches, it is essential to consider the role of CF in providing personalized recommendations and to explore new applications and scenarios where CF can be effectively utilized [34]. The evaluation of recommendation systems, which is discussed in the next section, is a crucial step in understanding their effectiveness and identifying areas for improvement. By leveraging advances in machine learning and optimization, we can develop more effective CF systems that can provide personalized recommendations to users and improve their overall experience [39].

### 2.3 Content-Based Filtering and Hybrid Approaches

Content-based filtering and hybrid approaches have emerged as viable alternatives or complements to collaborative filtering, offering a more nuanced understanding of user preferences and item attributes. These methods leverage the attributes of items and users to provide personalized recommendations, addressing some of the limitations of collaborative filtering, such as the cold start problem [22]. By incorporating additional information, content-based filtering and hybrid approaches can enhance the accuracy and diversity of recommendations, as demonstrated in [40] and [27].

Content-based filtering involves recommending items that are similar to the ones a user has liked or interacted with in the past [24]. This approach relies on the attributes of items, such as genres, authors, or categories, to identify patterns and relationships [26]. For instance, a user who has liked a particular movie genre may be recommended other movies within the same genre. Content-based filtering can be particularly effective in scenarios where there is limited user interaction data, as it can rely on item attributes to generate recommendations [41].

Hybrid approaches, on the other hand, combine multiple techniques, such as collaborative filtering and content-based filtering, to leverage their strengths and mitigate their weaknesses [42]. These approaches can be categorized into two main types: weighted hybrid and switching hybrid [29]. Weighted hybrid approaches assign weights to different techniques based on their performance, while switching hybrid approaches select the best technique based on the specific context or user [43].

One of the key benefits of hybrid approaches is their ability to address the cold start problem, where new users or items lack historical interaction data [44]. By incorporating content-based filtering, hybrid approaches can generate recommendations for new users or items based on their attributes, rather than relying solely on collaborative filtering [45].

Recent studies have also explored the use of deep learning techniques in content-based filtering and hybrid approaches [46]. These techniques can learn complex patterns and relationships in user and item data, enhancing the accuracy and diversity of recommendations [47]. For example, [48] proposes a hybrid deep model that combines content-based filtering and collaborative filtering to generate personalized recommendations.

Despite the advancements in content-based filtering and hybrid approaches, there are still challenges and limitations to be addressed [39]. One of the key challenges is the need for high-quality item attributes and user data, which can be difficult to obtain in certain scenarios [49]. Additionally, hybrid approaches can be complex to implement and require careful tuning of parameters to achieve optimal performance [50].

In conclusion, content-based filtering and hybrid approaches offer a range of benefits and opportunities for enhancing the accuracy and diversity of recommendations. By leveraging item attributes and user preferences, these methods can address some of the limitations of collaborative filtering and provide more nuanced and personalized recommendations. As the field continues to evolve, it is likely that we will see further advancements in content-based filtering and hybrid approaches, particularly with the integration of deep learning techniques and the development of more sophisticated hybrid models [51]. Future research should focus on addressing the challenges and limitations of these approaches, as well as exploring new applications and scenarios where content-based filtering and hybrid approaches can be effectively utilized [34].

### 2.4 Evaluation Metrics and Experimental Design

Evaluating the performance of recommendation systems is a crucial step in understanding their effectiveness and identifying areas for improvement. As discussed in the previous section, content-based filtering and hybrid approaches have emerged as viable alternatives or complements to collaborative filtering, offering a more nuanced understanding of user preferences and item attributes. The selection of appropriate evaluation metrics and experimental design plays a significant role in this process. The choice of evaluation metrics can significantly impact the perceived performance of a recommendation system, as highlighted in [52]. Commonly used metrics include precision, recall, F1-score, and A/B testing, each capturing different aspects of recommendation quality.

Precision, recall, and F1-score are widely used to evaluate the accuracy of recommendations [22]. Precision measures the proportion of relevant items among the recommended ones, while recall measures the proportion of recommended items among the relevant ones. The F1-score provides a balanced measure of both precision and recall. However, these metrics focus primarily on the accuracy of recommendations and may not fully capture other important aspects such as diversity, novelty, and user satisfaction. Diversity and novelty are essential for providing users with a wide range of options and preventing the over-recommendation of popular items [27]. Metrics such as intra-list similarity and catalog coverage can be used to evaluate the diversity of recommendations. Intra-list similarity measures the similarity between items in a recommendation list, while catalog coverage measures the proportion of items in the catalog that are recommended to at least one user.

Experimental design is another critical aspect of evaluating recommendation systems. A well-designed experiment should aim to minimize bias and ensure the reliability of the results. Techniques such as data splitting, sampling, and cross-validation can be used to achieve this [53]. Data splitting involves dividing the available data into training and testing sets, while sampling involves selecting a subset of users or items to participate in the experiment. Cross-validation involves repeating the experiment multiple times with different subsets of the data to ensure the results are consistent. The use of A/B testing is also becoming increasingly popular in the evaluation of recommendation systems [27]. A/B testing involves comparing the performance of two or more different recommendation algorithms or configurations on a random sample of users. This approach can provide valuable insights into the effectiveness of different algorithms and configurations in real-world settings.

In the context of the cold start problem, evaluating recommendation systems requires special consideration. The cold start problem refers to the challenge of providing recommendations for new users or items with limited or no interaction history. Techniques such as content-based filtering and hybrid approaches can be used to address this problem [54]. Recent studies have also highlighted the importance of considering the cold start problem in the evaluation of recommendation systems. The use of deep learning-based methods is becoming increasingly popular in the evaluation of recommendation systems [26]. These methods can learn complex patterns in user behavior and item attributes, providing more accurate and personalized recommendations. Furthermore, negative sampling techniques have shown promise in addressing data sparsity and the cold start problem [55], which will be discussed in the next section.

In conclusion, the evaluation of recommendation systems is a complex task that requires careful consideration of various metrics and experimental design techniques. By selecting the appropriate metrics and design, researchers and practitioners can gain a deeper understanding of the strengths and limitations of different recommendation algorithms and configurations, ultimately leading to the development of more effective and personalized recommendation systems. As noted in [48], the use of hybrid approaches and deep learning-based methods can provide significant improvements in recommendation accuracy and diversity. Further research is needed to explore the potential of these approaches and to develop new metrics and techniques for evaluating recommendation systems, which is essential for addressing the challenges discussed in the next section, including the cold start problem and data sparsity.

### 2.5 Cold Start Problem and Addressing Sparsity

The cold start problem is a significant challenge in recommendation systems, where new users or items are introduced, and there is limited interaction data available. This problem can be categorized into two types: new user cold start and new item cold start. The new user cold start problem occurs when a new user joins the system, and there is no interaction data available for that user. In this case, the system cannot provide personalized recommendations to the new user. On the other hand, the new item cold start problem occurs when a new item is added to the system, and there is no interaction data available for that item. In this case, the system cannot recommend the new item to users, even if it is relevant to their interests.

To address the cold start problem, several approaches have been proposed. One approach is to use content-based filtering, which recommends items based on their attributes or features [54]. Another approach is to use knowledge graph-based methods, which leverage the relationships between items and users to provide recommendations [56]. Transfer learning is also a popular approach, which uses pre-trained models and fine-tunes them on the target task [57].

Data sparsity is another significant challenge in recommendation systems, where the number of available ratings or interactions is limited compared to the number of users and items. This can lead to poor recommendation performance, especially for users or items with limited interaction data. To address data sparsity, several approaches have been proposed, including data augmentation, imputation, and dimensionality reduction techniques [58]. Data augmentation involves generating additional interaction data through techniques such as sampling or simulation [59]. Imputation involves filling in missing interaction data using statistical or machine learning-based methods [60]. Dimensionality reduction techniques involve reducing the number of features or dimensions in the interaction data to improve recommendation performance [61].

Recent studies have also explored the use of negative sampling techniques to address data sparsity and the cold start problem [55]. Negative sampling involves selecting a subset of negative samples from the available interaction data to improve recommendation performance. This can help to reduce the impact of data sparsity and improve the accuracy of recommendations. However, the choice of negative sampling technique can have a significant impact on recommendation performance, and several studies have explored different techniques, including random sampling, popularity-based sampling, and knowledge graph-based sampling [11].

In conclusion, the cold start problem and data sparsity are significant challenges in recommendation systems, requiring innovative solutions to address. Several approaches have been proposed to address these challenges, including content-based filtering, knowledge graph-based methods, transfer learning, data augmentation, imputation, and dimensionality reduction techniques. Recent studies have also explored the use of negative sampling techniques to improve recommendation performance. Further research is needed to develop more effective solutions to these challenges and to improve the overall performance of recommendation systems [62]. By addressing these challenges, recommendation systems can provide more accurate and personalized recommendations to users, leading to improved user experience and increased engagement [63].

### 2.6 Advanced Topics and Future Directions

Recent advancements in recommendation systems have led to the development of more sophisticated and effective methods for personalized recommendation, building on the foundations established in addressing the cold start problem and data sparsity. One key area of research is the incorporation of side information, such as user demographics, item attributes, and contextual data, to enhance the accuracy and diversity of recommendations [64]. For instance, [44] proposes a niche approach that applies interrelationship mining to identify new binary relations between item attributes, thereby enriching the available information on new items. This approach is particularly useful in addressing the new item cold start problem, where there is limited interaction data available for new items.

Another important direction is contextual awareness, which involves incorporating contextual information, such as location, time, and social networks, to provide more accurate and relevant recommendations [65]. For example, [66] proposes a meta-learning-based approach that captures the dynamic transition patterns among users with a translation-based architecture, enabling fast learning for cold-start users with limited interactions. Furthermore, [67] introduces a classification-based knowledge base completion method that adopts a modularized design and attempts to find hard negative samples to train a powerful classifier for missing link prediction, highlighting the importance of negative sampling in recommendation systems.

Explainability is also a crucial aspect of recommendation systems, as it enables users to understand the reasoning behind the recommended items [68]. Techniques such as [69] propose a meta-learning-based framework that captures meta users' preference and entities' knowledge for cold-start recommendations, providing a more transparent and interpretable recommendation process. The incorporation of explainability techniques can help to build trust with users and improve the overall effectiveness of recommendation systems.

The incorporation of deep learning techniques has also revolutionized the field of recommendation systems [34]. For instance, [70] proposes a novel meta-learning recommender called task-adaptive neural process (TaNP) that directly maps the observed interactions of each user to a predictive distribution, sidestepping some training issues in gradient-based meta-learning models. These advancements have the potential to significantly improve the performance of recommendation systems, particularly in addressing the cold start problem and data sparsity.

Despite the significant advancements in recommendation systems, there are still several challenges and open issues that need to be addressed [71]. For example, [72] systematically reviews various negative sampling methods and their contributions to the success of knowledge graph representation learning, highlighting the importance of generating high-quality negative samples. Furthermore, [73] proposes a stabilized doubly robust learning approach that retains double robustness while having bounded bias, variance, and generalization error bound simultaneously under inaccurate imputed errors and arbitrarily small propensities. These challenges and open issues must be addressed to further improve the effectiveness and efficiency of recommendation systems.

In conclusion, the field of recommendation systems is rapidly evolving, with a focus on incorporating side information, contextual awareness, explainability, and deep learning techniques to provide more accurate and diverse recommendations. As researchers continue to explore new approaches and techniques, it is essential to address the challenges and open issues in the field, such as negative transfer, data sparsity, and cold-start problems. By synthesizing the existing knowledge and identifying emerging trends and challenges, we can develop more effective and efficient recommendation systems that provide personalized and relevant recommendations to users [74]. Future research directions may include the development of more sophisticated meta-learning approaches, the incorporation of multimodal data, and the application of recommendation systems to emerging areas, such as healthcare and education [75].

## 3 Negative Sampling Techniques

### 3.1 Introduction to Negative Sampling Techniques

Negative sampling techniques are a crucial component of recommendation systems, enabling the efficient selection of negative instances from large datasets to improve model performance. The concept of negative sampling involves identifying a subset of negative examples from a vast pool of potential candidates, which is essential for training recommendation models, especially in scenarios where explicit negative feedback is scarce [76]. The importance of negative sampling lies in its ability to enhance model accuracy and robustness by providing a more comprehensive understanding of user preferences [3].

Various negative sampling techniques have been proposed, each with its strengths and limitations. Random sampling, for instance, is a straightforward approach that selects negative samples randomly from the pool of potential candidates [2]. However, this method may not be effective in capturing informative negative samples, especially in scenarios where the number of negative samples is large. To address this issue, techniques such as popularity-based sampling [77] and knowledge graph-based sampling [78] have been developed. These methods aim to select negative samples that are more informative and relevant to the user's preferences.

Recent studies have also explored the use of advanced techniques, such as adversarial sampling [79] and reinforcement learning-based sampling [18], to improve the quality of negative samples. These methods have shown promising results in enhancing model performance and robustness. Moreover, the use of negative sampling in deep learning-based recommendation models has also been investigated [14], highlighting the potential of these models in improving recommendation accuracy.

Despite the advancements in negative sampling techniques, several challenges and limitations remain. One of the primary concerns is the selection of informative negative samples, which can be time-consuming and computationally expensive [14]. Furthermore, the quality of negative samples can significantly impact model performance, and therefore, it is essential to develop techniques that can effectively identify high-quality negative samples [80].

The evolution of negative sampling techniques has also led to the development of new methods, such as Bayesian negative sampling [81] and layer-diverse negative sampling [82]. These methods have shown promising results in improving model performance and robustness, highlighting the importance of continued research in this area. Moreover, the application of negative sampling in various domains, such as recommender systems [10] and natural language processing [19], has also been explored.

In conclusion, negative sampling techniques play a vital role in improving the performance of recommendation systems. The development of effective negative sampling methods is essential for enhancing model accuracy and robustness. While various techniques have been proposed, challenges and limitations remain, highlighting the need for continued research in this area. Future directions include the development of more efficient and effective negative sampling methods, as well as the exploration of new applications and domains [11]. As the field continues to evolve, it is essential to investigate new techniques and methods that can improve the quality of negative samples and enhance model performance [15].

### 3.2 Basic Negative Sampling Methods

Basic negative sampling methods are the foundation of recommendation systems, providing a starting point for the development of more advanced techniques. These methods involve selectively sampling negative instances from a large dataset to improve the accuracy and efficiency of recommendations. One of the most straightforward approaches is random sampling, where negative samples are chosen randomly from the set of uninteracted items. This method is simple to implement but can be inefficient, as it may not capture the most informative negative samples. For instance, random sampling may select negative samples that are not representative of the user's preferences, leading to suboptimal model performance [2].

Another basic method is popularity-based sampling, which selects negative samples based on their popularity. The idea behind this approach is that popular items are more likely to be relevant to a user, and therefore, sampling negative instances from popular items can help improve the recommendation model. However, this method can suffer from the problem of popularity bias, where the model tends to recommend popular items over less popular ones. To mitigate this issue, techniques such as popularity-aware item weighting can be employed to reduce the bias towards popular items [77].

Both random and popularity-based sampling methods have their limitations. Random sampling can be inefficient, while popularity-based sampling can introduce bias into the model. To address these limitations, more advanced methods have been proposed, such as [27] and [56]. These methods aim to balance the trade-off between accuracy and diversity in recommendations. Recent studies have also explored the use of side information, such as item attributes and user demographics, to improve negative sampling [83]. For example, [84] proposes a method to infer networks of substitutable and complementary products, which can be used to select negative samples that are more informative.

The development of basic negative sampling methods has paved the way for the exploration of more advanced techniques, including the use of deep learning to improve negative sampling [26]. This approach can learn complex patterns in user behavior and item relationships, which can help select more informative negative samples. Furthermore, the integration of negative sampling with deep learning-based recommendation models has shown promising results in improving recommendation accuracy [14].

Despite the advancements in negative sampling methods, there are still challenges to be addressed. For example, [35] and [36] have highlighted the issue of popularity bias in recommendation systems, which can be exacerbated by negative sampling methods. To address this issue, [77] proposes a method to weight items based on their popularity, which can help reduce the bias towards popular items. As noted in [51], the development of effective negative sampling methods is crucial for improving the performance of recommendation systems.

In conclusion, basic negative sampling methods, such as random and popularity-based sampling, provide a foundation for more advanced techniques. While these methods have limitations, recent studies have proposed various approaches to improve negative sampling, including the use of side information and deep learning. Addressing the challenges of popularity bias and diversity in recommendations remains an open problem, and future research directions include the development of more advanced methods that can balance the trade-off between accuracy and diversity. The exploration of new approaches and techniques, such as [85] and [86], will be essential in improving the accuracy and efficiency of recommendation systems, ultimately enhancing the user experience.

### 3.3 Advanced Negative Sampling Techniques

Advanced negative sampling techniques have been developed to address the limitations of basic methods, such as random sampling and popularity-based sampling. These techniques aim to improve the accuracy and diversity of recommendations by selectively sampling negative instances. One such approach is adversarial sampling [58], which uses adversarial techniques to generate hard negative samples that challenge the model and improve its robustness. 

Another approach is reinforcement learning-based sampling [51], which employs reinforcement learning to dynamically select negative samples based on their potential impact on model performance. 

Graph convolutional network-based sampling [87] is another advanced technique that leverages graph structures to identify informative negative samples. 

In addition to these techniques, [29] provides a comprehensive survey of neighborhood-based methods for recommender systems, which can be used to improve the accuracy and diversity of recommendations. [30] also discusses the importance of implicit feedback in recommender systems, and provides a framework for incorporating implicit feedback into recommendation models.

The strengths and limitations of these advanced techniques are summarized in [39], which provides a critical analysis of the current state of recommender systems research. 

In terms of future directions, [34] provides a comprehensive survey of deep meta-learning based recommendation methods, which have the potential to improve the performance of recommendation models in scenarios where data is limited. 

Overall, advanced negative sampling techniques have the potential to significantly improve the accuracy and diversity of recommendations in recommender systems. By selectively sampling negative instances, these techniques can improve the robustness of recommendation models and adapt to changing user preferences over time. 

Recent studies have also explored the use of deep learning models for negative sampling, such as [46]. 

In conclusion, advanced negative sampling techniques have the potential to significantly improve the accuracy and diversity of recommendations in recommender systems. Further research is needed to evaluate the effectiveness of these techniques in different scenarios, and to develop more efficient and scalable methods for sampling negative instances.

### 3.4 Deep Learning for Negative Sampling

Deep learning models have been increasingly applied to negative sampling due to their ability to learn complex patterns and relationships, as evident in the work of [42]. This approach has shown promising results, particularly in addressing the cold start problem and improving the diversity of recommendations. For instance, [88] demonstrates how social exposure can be used to improve the accuracy of recommendations, while [43] highlights the importance of incorporating contextual information into deep learning-based recommender systems.

The use of deep learning models in negative sampling offers several advantages, including the ability to learn representations from raw data and model complex user behaviors. This is evident in the work of [48], where the authors propose a hybrid deep model that combines the strengths of collaborative filtering and content-based filtering to provide personalized recommendations. Furthermore, [89] demonstrates the effectiveness of deep learning models in improving the accuracy of recommendations in multi-criteria recommender systems.

However, the application of deep learning models in negative sampling also poses several challenges and limitations. One of the key challenges is the risk of overfitting, particularly when dealing with large and complex datasets, as highlighted in [2]. Another challenge is the need for large amounts of training data, which can be a limitation in scenarios where data is scarce, as noted in [44]. To address these challenges, researchers have explored various techniques, such as regularization, early stopping, and ensemble methods, to prevent overfitting and improve the performance of deep learning models in negative sampling.

Recent advancements in deep learning-based negative sampling have focused on the use of attention mechanisms and graph neural networks. For instance, [90] provides a comprehensive survey of graph-based recommender systems, highlighting the potential of graph neural networks in modeling complex relationships between users and items. Additionally, [37] demonstrates the effectiveness of attention mechanisms in improving the accuracy and diversity of recommendations. The use of these techniques has shown promising results in improving the performance of deep learning models in negative sampling, and it is likely that we will see further innovations in this area in the future.

In conclusion, deep learning models have shown promising results in negative sampling, particularly in addressing the cold start problem and improving the diversity of recommendations. While there are challenges and limitations to be addressed, recent advancements in attention mechanisms and graph neural networks have improved the performance of deep learning models in negative sampling. As the field continues to evolve, it is likely that we will see further innovations in deep learning-based negative sampling, particularly in the use of multimodal data and transfer learning, as noted in [91]. Overall, the use of deep learning models in negative sampling has the potential to significantly improve the accuracy and diversity of recommendations, and it is likely that we will see further innovations in this area in the future, ultimately leading to more effective evaluation and application of negative sampling techniques, as discussed in the following section.

### 3.5 Evaluation and Challenges of Negative Sampling Techniques

Evaluating the effectiveness of negative sampling techniques is crucial for developing robust recommendation systems. The primary goal of negative sampling is to select a subset of negative instances from a large pool of candidates, which can efficiently train a model to distinguish between positive and negative items [49]. However, the choice of evaluation metric significantly influences the assessment of negative sampling strategies, and there is no one-size-fits-all solution [62].

Comparative analysis of different negative sampling approaches reveals that each method has its strengths and limitations. For instance, random sampling is simple and efficient but may not provide informative negative samples [55]. Popularity-based sampling, on the other hand, can capture popular items but may introduce bias towards frequently interacted items [92]. Advanced techniques, such as adversarial sampling and reinforcement learning-based sampling, have shown promising results in improving model performance but often require careful tuning of hyperparameters and can be computationally expensive [93].

One of the significant challenges in negative sampling is the bias-variance trade-off. While increasing the number of negative samples can reduce bias, it may also introduce variance, leading to overfitting or underfitting [94]. To mitigate this issue, techniques such as regularization, early stopping, and ensemble methods can be employed [60]. Moreover, the cold start problem, where new users or items lack historical interaction data, poses a significant challenge for negative sampling techniques [54].

Recent advances in negative sampling research have focused on developing more efficient and scalable methods, incorporating side information, and addressing emerging challenges such as multi-modal recommendation and explainability [63]. For instance, graph-based negative sampling techniques have shown promise in modeling complex relationships between items and users [88]. Additionally, the use of attention mechanisms and graph neural networks has been explored to improve the performance of negative sampling techniques [95].

Despite the progress made in negative sampling research, several open challenges remain. For example, developing methods that can effectively handle high-dimensional data, addressing the issue of class imbalance, and improving the interpretability of negative sampling techniques are essential future directions [58]. Furthermore, the development of more robust evaluation metrics and protocols is necessary to ensure fair comparison and reproducibility of results [96].

In conclusion, evaluating and addressing the challenges of negative sampling techniques are crucial for developing robust recommendation systems. By understanding the strengths and limitations of different approaches, addressing emerging challenges, and exploring new research directions, we can improve the performance and efficiency of negative sampling techniques [11]. Future research should focus on developing more efficient, scalable, and interpretable negative sampling techniques that can handle complex relationships between users and items [97].

### 3.6 Applications and Case Studies of Negative Sampling

Negative sampling techniques have been widely applied in various domains and scenarios, demonstrating their versatility and effectiveness in improving the performance of recommendation systems. As discussed in the previous section, the development of efficient and scalable negative sampling methods has paved the way for their application in real-world recommendation systems. One of the key applications of negative sampling is in e-commerce platforms, where it is used to recommend products to users based on their past purchases and browsing history [98]. For instance, a study by [99] showed that negative sampling can be used to improve the accuracy of product recommendations by selecting informative negative samples. This is particularly important in e-commerce, where the quality of recommendations can have a significant impact on user engagement and conversion rates.

In addition to e-commerce, negative sampling has also been applied in social media platforms to recommend posts, ads, or friends [100]. For example, a study by [74] showed that negative sampling can be used to improve the performance of recommendation algorithms in social media platforms by handling imbalanced user feedback. The use of negative sampling in social media platforms can help to address the challenges of user cold-start and item cold-start problems, where there is limited user interaction data available.

Furthermore, negative sampling has been used to address the cold-start problem in recommendation systems [101]. For instance, a study by [44] showed that negative sampling can be used to improve the performance of recommendation algorithms for new items by selecting informative negative samples. This is particularly important in scenarios where new items are constantly being added to the system, and there is limited interaction data available.

The application of negative sampling in real-world recommendation systems has also been explored in various studies. For example, a study by [67] demonstrated the effectiveness of negative sampling in improving the performance of knowledge graph-based recommendation algorithms. These studies demonstrate the potential of negative sampling to improve the performance of recommendation systems in a variety of domains and scenarios.

In conclusion, negative sampling techniques have been widely applied in various domains and scenarios, demonstrating their versatility and effectiveness in improving the performance of recommendation systems. The application of negative sampling in real-world recommendation systems has shown promising results, and future research directions include exploring new negative sampling strategies and applying negative sampling to emerging areas such as multi-modal recommendation and explainable recommendation [34]. As noted by [72], negative sampling is a crucial component of knowledge graph-based recommendation algorithms, and its effectiveness has a significant impact on the performance of recommendation systems.

## 4 Deep Learning for Negative Sampling

### 4.1 Introduction to Deep Learning Architectures for Recommendation Systems

Deep learning models have revolutionized the field of recommendation systems, offering a powerful approach to learn complex patterns and relationships in user-item interactions. The ability of deep learning architectures to automatically learn representations from raw data has made them particularly appealing for recommendation tasks, where traditional methods often rely on hand-crafted features. In this subsection, we delve into the basic deep learning architectures used in recommendation systems, including neural collaborative filtering and deep matrix factorization, highlighting their strengths, limitations, and applications.

Neural collaborative filtering (NCF) [4] is a prominent deep learning approach for recommendation systems, which integrates the strengths of collaborative filtering and neural networks. NCF models user-item interactions as a neural network, learning non-linear representations of users and items to predict ratings or rankings. The key advantage of NCF lies in its ability to capture complex, high-order relationships between users and items, leading to improved recommendation accuracy. However, NCF models can be computationally expensive to train, particularly for large-scale datasets, and may require careful tuning of hyperparameters to achieve optimal performance.

Deep matrix factorization (DMF) [5] is another deep learning architecture used in recommendation systems, which extends traditional matrix factorization techniques by learning non-linear representations of users and items. DMF models user-item interactions as a neural network, factorizing the user-item interaction matrix into lower-dimensional representations of users and items. The strengths of DMF lie in its ability to handle large-scale datasets and its flexibility in incorporating side information, such as item attributes or user demographics. However, DMF models can be sensitive to the choice of hyperparameters and may require careful regularization to prevent overfitting.

Recent studies have also explored the application of negative sampling techniques in deep learning-based recommendation systems. For example, [5] proposes a mixed negative sampling strategy, which combines the strengths of different negative sampling methods to improve the accuracy of recommendation models. Other works, such as [2] and [14], have investigated the impact of negative sampling on the performance of deep learning-based recommendation models, highlighting the importance of careful sampling strategies in achieving optimal results.

In addition to NCF and DMF, other deep learning architectures, such as recurrent neural networks (RNNs) and graph neural networks (GNNs), have been applied to recommendation systems. RNNs have been used to model sequential user behavior, capturing temporal relationships between user-item interactions. GNNs have been used to model complex relationships between items, capturing structural information in item graphs. These architectures offer promising directions for future research, particularly in applications where sequential or structural relationships are critical.

Despite the advances in deep learning-based recommendation systems, several challenges and limitations remain. One key challenge is the need for large amounts of training data, which can be difficult to obtain in practice. Another challenge is the risk of overfitting, particularly in models with large numbers of parameters. To address these challenges, researchers have explored techniques such as transfer learning, meta-learning, and few-shot learning, which offer promising directions for improving the efficiency and effectiveness of deep learning-based recommendation systems.

In conclusion, deep learning architectures have revolutionized the field of recommendation systems, offering powerful approaches to learn complex patterns and relationships in user-item interactions. While challenges and limitations remain, the strengths of deep learning models, combined with careful sampling strategies and innovative architectures, offer promising directions for future research and applications. As the field continues to evolve, we can expect to see further innovations in deep learning-based recommendation systems, particularly in applications where complex relationships and sequential behavior are critical. Further studies will be essential in advancing our understanding of the role of negative sampling in deep learning-based recommendation systems.

### 4.2 Deep Learning Techniques for Negative Sampling

Deep learning techniques have revolutionized the field of negative sampling in recommendation systems, offering a wide range of methods to improve the accuracy and efficiency of recommendations. As discussed in the previous section, deep learning architectures such as neural collaborative filtering and deep matrix factorization have been successfully applied to recommendation systems, and negative sampling has emerged as a crucial component in these models. One of the key approaches to negative sampling is adversarial sampling, which involves generating hard negative samples that challenge the model and improve its robustness [58]. Adversarial sampling methods, such as [88], have shown promising results in improving the performance of recommendation models. However, these methods can be computationally expensive and may require significant tuning of hyperparameters.

In addition to adversarial sampling, reinforcement learning-based sampling has also gained significant attention in recent years. This approach involves dynamically selecting negative samples based on their potential impact on model performance [102]. Reinforcement learning-based methods, such as [103], have been shown to be effective in balancing exploration and exploitation in negative sampling. These methods can adapt to changing user preferences and item distributions, making them suitable for real-world applications. Furthermore, graph convolutional network-based sampling has also been explored, which can effectively model complex relationships between items and users, leading to improved negative sampling performance [26]. Graph-based methods, such as [104], can incorporate side information, such as item attributes and user demographics, to further enhance recommendation accuracy.

Recent studies have also explored the use of attention mechanisms and graph neural networks for negative sampling [26]. Attention-based methods, such as [37], can selectively focus on relevant items and users, improving the efficiency of negative sampling. Graph neural network-based methods, such as [105], can learn complex patterns and relationships in user-item interactions, leading to more accurate negative sampling. These advancements have paved the way for further research in negative sampling, and the following section will delve into the latest developments and applications of deep learning-based negative sampling methods.

Despite the advances in deep learning techniques for negative sampling, there are still several challenges and open issues that need to be addressed [39]. One of the key challenges is the need for large amounts of labeled data, which can be difficult to obtain in real-world applications. Another challenge is the risk of overfitting, which can occur when models are trained on limited data. To address these challenges, future research should focus on developing more efficient and scalable negative sampling methods, as well as exploring new techniques for handling limited data and preventing overfitting. By building on the foundations established in this section, researchers can continue to push the boundaries of negative sampling in recommendation systems, leading to improved recommendation performance and enhanced user experiences [106]. Future research should focus on addressing the challenges and open issues in negative sampling, such as the need for large amounts of labeled data and the risk of overfitting, to further advance the field [107].

### 4.3 Recent Advancements in Deep Learning-Based Negative Sampling

Recent advancements in deep learning-based negative sampling have led to significant improvements in the accuracy and efficiency of recommendation systems. One of the key developments in this area is the use of attention mechanisms, which allow the model to focus on the most relevant items when generating negative samples [108]. For example, the work in [48] demonstrates how attention mechanisms can be used to improve the performance of deep learning-based negative sampling models. Additionally, graph neural networks have been shown to be effective in modeling complex relationships between items and users, and can be used to generate high-quality negative samples [87].

Another important development in deep learning-based negative sampling is the use of adversarial training methods, which involve training the model to generate negative samples that are indistinguishable from positive samples [2]. This approach has been shown to improve the robustness and accuracy of recommendation models, and can be used in conjunction with other techniques such as attention mechanisms and graph neural networks. For instance, the work in [50] proposes a fast adaptively weighted matrix factorization approach that incorporates adversarial training to improve the performance of recommendation models.

The use of deep learning-based negative sampling methods has also been explored in the context of cold start problems, where there is limited or no interaction data available for new users or items [28]. In this setting, deep learning-based methods can be used to generate negative samples that are tailored to the specific user or item, and can help to improve the performance of recommendation models. For example, the work in [51] proposes a deep learning-based approach for sequential recommendation that incorporates negative sampling to improve the performance of recommendation models in cold start scenarios.

Despite the advancements in deep learning-based negative sampling, there are still several challenges and opportunities for future research in this area. One of the key challenges is the need for more efficient and scalable methods, as deep learning-based models can be computationally expensive to train and deploy [26]. Another challenge is the need for more effective methods for incorporating side information, such as item attributes and user demographics, into deep learning-based negative sampling models [83].

In terms of future directions, one promising area of research is the use of transfer learning and meta-learning techniques to improve the performance of deep learning-based negative sampling models [34]. These techniques involve training the model on a related task or dataset, and then fine-tuning it on the target task or dataset. This can help to improve the performance of the model, especially in scenarios where there is limited training data available. Another promising area of research is the use of multimodal data, such as text, images, and audio, to improve the performance of deep learning-based negative sampling models [109].

Overall, deep learning-based negative sampling has the potential to significantly improve the performance of recommendation systems, and there are many exciting opportunities for future research in this area. By exploring new techniques and architectures, such as attention mechanisms, graph neural networks, and adversarial training methods, researchers can develop more accurate and efficient models that can handle complex scenarios and provide personalized recommendations to users [110]. Additionally, the use of deep learning-based negative sampling methods can be extended to other areas, such as natural language processing and computer vision, where the goal is to generate high-quality negative samples that can improve the performance of models [43].

### 4.4 Applications of Deep Learning-Based Negative Sampling

Deep learning-based negative sampling has been widely applied in various domains, including e-commerce, social media, and content streaming platforms, with significant improvements in recommending accurate and personalized items to users. For instance, in e-commerce, [22] and [26] have demonstrated the effectiveness of deep learning-based negative sampling in recommending products to users by leveraging user-item interaction data and item attributes. However, e-commerce platforms also face challenges such as cold start problems, where new users or items lack historical interaction data, which can be addressed through attribute-driven active learning and hybrid approaches that combine collaborative filtering with content-based filtering, as proposed in [54] and [111].

Similarly, in social media, deep learning-based negative sampling has been used to recommend posts, ads, or friends to users, with studies such as [112] showing that post-click feedback can be leveraged to improve the training and evaluation of content recommenders. Additionally, [113] has proposed a hybrid approach that incorporates both collaborative filtering and content-based filtering to recommend movies to users. Nevertheless, social media platforms also face challenges such as popularity bias, where popular items are recommended frequently, while less popular items are recommended rarely, which can be mitigated through popularity-aware item weighting approaches, as proposed in [77].

In content streaming platforms, deep learning-based negative sampling has been used to recommend movies, TV shows, or music to users, with studies such as [114] demonstrating the effectiveness of non-negative matrix factorization and graph total variation in recommending songs to users. However, content streaming platforms also face challenges such as the need to balance accuracy and diversity in recommendations, which can be addressed through approaches that reconcile the trade-off between accuracy and diversity, as proposed in [115] and [116].

Despite the successes of deep learning-based negative sampling in various domains, there are still challenges and limitations that need to be addressed, such as cold start problems, popularity bias, and filter bubbles. For example, [117] has shown that collaborative filtering can suffer from stereotyping, where users are recommended items that are similar to those they have already liked or interacted with, which can be mitigated through multi-factor sequential re-ranking approaches, as proposed in [37]. Furthermore, [106] has shown that filter bubbles can occur in short-video recommendation, where users are exposed to narrow content within their broad interests.

To overcome these challenges, future research should focus on developing more effective and efficient deep learning-based negative sampling approaches that can balance accuracy and diversity in recommendations. As [58] has pointed out, diversity and novelty are important aspects of recommendation systems, and future research should prioritize these aspects to improve the overall user experience. Additionally, [118] has highlighted the importance of correcting for multifactorial bias in recommender systems, which is a crucial aspect of deep learning-based negative sampling. By addressing these challenges and limitations, deep learning-based negative sampling can continue to play a vital role in improving the accuracy and diversity of recommendations in various domains, ultimately leading to more effective evaluation and benchmarking methods, as discussed in the following section.

### 4.5 Evaluation Metrics and Benchmarking for Deep Learning-Based Negative Sampling

Evaluating the performance of deep learning-based negative sampling methods is crucial for understanding their effectiveness in improving recommendation systems. The choice of evaluation metrics and benchmarking methods plays a significant role in assessing the performance of these methods [58]. Commonly used metrics include precision, recall, F1-score, and A/B testing, which provide insights into the accuracy and robustness of the models [119]. However, these metrics may not capture the entire picture, especially when dealing with complex scenarios such as cold start problems or multi-modal recommendation systems [120].

To address these challenges, researchers have proposed various evaluation protocols and metrics, such as the use of inverse propensity scoring (IPS) to estimate the expected reward of a recommendation policy [121]. Additionally, metrics like normalized discounted cumulative gain (NDCG) and mean average precision (MAP) have been widely adopted to evaluate the ranking quality of recommendation systems [122]. These metrics provide a more comprehensive understanding of the models' performance, but they may still be biased towards popular items or users [123].

Recent studies have also emphasized the importance of considering beyond-accuracy metrics, such as diversity, novelty, and fairness, when evaluating recommendation systems [63]. These metrics can help identify potential biases and limitations of the models, providing a more nuanced understanding of their performance [124]. Furthermore, the use of simulated environments and synthetic data has become increasingly popular for evaluating and benchmarking recommendation systems, allowing for more controlled and reproducible experiments [97].

In the context of deep learning-based negative sampling, researchers have proposed various benchmarking methods, such as the use of publicly available datasets and open-source libraries, to facilitate the comparison and evaluation of different models [96]. These benchmarking methods can help identify the strengths and weaknesses of different models and provide insights into their performance on various tasks and datasets. However, the choice of benchmarking method and evaluation metric depends on the specific problem and dataset, and researchers should carefully consider these factors when designing and evaluating their models [125].

In conclusion, evaluating the performance of deep learning-based negative sampling methods requires a comprehensive and nuanced approach, considering multiple metrics and benchmarking methods. By acknowledging the limitations and biases of different evaluation protocols and metrics, researchers can design more effective and robust models that improve the accuracy and diversity of recommendation systems [115]. Future research should continue to explore and develop new evaluation metrics and benchmarking methods, incorporating beyond-accuracy metrics and simulated environments to provide a more complete understanding of the performance of deep learning-based negative sampling methods [126]. As noted in [55], the development of more efficient and effective negative sampling methods is crucial for improving the performance of recommendation systems. Similarly, [127] highlights the importance of considering false positives in session-based recommendation systems. Overall, the evaluation and benchmarking of deep learning-based negative sampling methods is a critical area of research, with significant implications for the development of more accurate and diverse recommendation systems [128].

### 4.6 Future Directions and Open Challenges in Deep Learning-Based Negative Sampling

The field of deep learning-based negative sampling has experienced significant growth in recent years, with various approaches being proposed to improve the efficiency and effectiveness of recommendation systems [98]. As the previous discussion on evaluation metrics and benchmarking methods has highlighted, the development of more efficient and effective negative sampling methods is crucial for improving the performance of recommendation systems. Despite the advancements, there are still several open challenges and future directions that need to be addressed. One of the primary challenges is the need for more efficient and scalable methods, as current approaches can be computationally expensive and may not be suitable for large-scale recommendation systems. To address this challenge, researchers have proposed the use of techniques such as distributed computing and parallel processing to speed up the computation process [74].

In addition to improving efficiency, another future direction is the incorporation of side information, such as user demographics and item attributes, into deep learning-based negative sampling models [129]. This can be achieved through the use of multi-task learning frameworks, where the model is trained to predict both the user's preference and the side information [34]. The use of side information can help to improve the accuracy of recommendations, especially in cold-start scenarios where there is limited interaction data available [65]. Furthermore, the use of techniques such as transfer learning and meta-learning can help to improve the performance of deep learning-based negative sampling models in cold-start scenarios [69].

The use of generative models, such as generative adversarial networks (GANs) and variational autoencoders (VAEs), is another future direction in deep learning-based negative sampling [75]. These models can be used to generate synthetic user-item interaction data, which can help to improve the performance of recommendation systems, especially in scenarios where there is limited interaction data available [67]. Moreover, the use of techniques such as reinforcement learning and evolutionary algorithms can help to improve the performance of deep learning-based negative sampling models [130]. By exploring these future directions, researchers can develop more effective and efficient recommendation systems that can provide personalized recommendations to users.

Despite the advancements in deep learning-based negative sampling, there are still several open challenges that need to be addressed. One of the primary challenges is the issue of negative transfer, where the use of negative sampling can lead to a decrease in the performance of the recommendation system [71]. To address this challenge, researchers have proposed the use of techniques such as adversarial training and robust optimization [73]. Another challenge is the issue of data sparsity, where there is limited interaction data available for certain users or items [68]. To address this challenge, researchers have proposed the use of techniques such as data augmentation and transfer learning [131]. By addressing these open challenges, researchers can develop more effective and efficient recommendation systems that can provide personalized recommendations to users, ultimately enhancing the overall user experience.

In conclusion, the field of deep learning-based negative sampling is rapidly evolving, with several future directions and open challenges that need to be addressed. The incorporation of side information, the use of generative models, and the development of more efficient and scalable methods are some of the key areas of research that can help to improve the performance of recommendation systems. Additionally, the use of techniques such as transfer learning, meta-learning, and reinforcement learning can help to improve the performance of deep learning-based negative sampling models in cold-start scenarios. By addressing the open challenges and exploring the future directions, researchers can develop more effective and efficient recommendation systems that can provide personalized recommendations to users [132]. As noted in [72], the quality of negative samples has a significant impact on the performance of recommendation systems, and therefore, developing effective negative sampling strategies is crucial for improving the performance of recommendation systems. These advancements will pave the way for the next generation of recommendation systems, which will be discussed in the following section.

## 5 Applications and Case Studies

### 5.1 Case Studies of Negative Sampling in Various Domains

Negative sampling has been widely applied in various domains to improve the accuracy and diversity of recommendations. In e-commerce, for instance, [3] has demonstrated the effectiveness of negative sampling in recommending products to users based on their past purchases and browsing history. Similarly, in social media, [4] has shown that negative sampling can be used to recommend posts, ads, or friends to users by leveraging the large amount of uninteracted content.

In content streaming platforms, [78] has highlighted the importance of negative sampling in recommending movies, TV shows, or music to users by considering the vast catalog of content that a user has not watched or listened to. Moreover, [5] has demonstrated the effectiveness of mixed negative sampling in improving the performance of two-tower neural networks in recommendation systems.

Furthermore, [6] has provided a comprehensive review of negative sampling methods in graph representation learning, highlighting their strengths and limitations. [15] has also demonstrated the effectiveness of negative sampling in hyperlink prediction, which is crucial in many web-based applications.

In addition, [10] has shown that importance sampling can be used to select high-quality negative samples, which can improve the performance of recommendation models. [18] has also demonstrated the effectiveness of stochastic negative mining in improving the performance of recommendation models.

Moreover, [14] has highlighted the importance of negative sampling in context-aware recommendation, which is crucial in many real-world applications. [128] has also demonstrated the effectiveness of negative sampling in evaluating neural sequential item recommendation models.

Finally, [11] has provided a comprehensive review of negative sampling, highlighting its theory, applications, and future directions. [72] has also provided a comprehensive review of negative sampling methods in knowledge graph representation learning, highlighting their strengths and limitations.

In conclusion, negative sampling has been widely applied in various domains to improve the accuracy and diversity of recommendations. The effectiveness of negative sampling has been demonstrated in various studies, including [133], [134], and [135]. Future research directions include exploring new negative sampling methods, such as [82] and [136], and applying negative sampling to new domains, such as [137] and [138].

### 5.2 Negative Sampling in Cold-Start Scenarios

Negative sampling plays a vital role in addressing cold-start scenarios, where new users or items are introduced, and there is limited interaction data available, as highlighted in the previous discussion on the applications of negative sampling in various domains. In such scenarios, traditional collaborative filtering methods often struggle to provide accurate recommendations due to the lack of historical interaction data [22]. This limitation can be mitigated by leveraging negative sampling techniques, which can help improve the accuracy and diversity of recommendations in cold-start scenarios.

One of the key challenges in cold-start scenarios is the new user cold-start problem, where a new user has no interaction history [25]. In this case, negative sampling can help by leveraging the interactions of similar users to recommend items to the new user [88]. By selectively sampling negative instances from the large item set, negative sampling can improve the accuracy and efficiency of recommendations for new users. Furthermore, negative sampling can be used in conjunction with other techniques, such as user-based collaborative filtering, to improve the performance of recommendation models in cold-start scenarios.

Another challenge in cold-start scenarios is the new item cold-start problem, where a new item has no interaction history [54]. In this case, negative sampling can help by considering the attributes and features of the new item, as well as the interactions of similar items [139]. Hybrid approaches that combine user-based and item-based negative sampling strategies can also be effective in addressing cold-start scenarios [140]. These approaches can help to improve the accuracy and diversity of recommendations by leveraging the strengths of both user-based and item-based negative sampling techniques.

In addition to these approaches, negative sampling can also be used in conjunction with other techniques, such as meta-learning [34] and causal inference [38], to improve the accuracy and efficiency of recommendations in cold-start scenarios. By integrating negative sampling with these techniques, researchers can develop more effective and efficient recommendation models that can handle cold-start scenarios. Overall, negative sampling is a crucial technique in addressing cold-start scenarios in recommendation systems, and its effectiveness has been demonstrated in various studies. As the field of recommendation systems continues to evolve, it is likely that negative sampling will remain a key area of research and development, particularly in the context of cold-start scenarios, which will be further discussed in the subsequent section on the technical challenges and practical considerations of negative sampling in recommendation systems.

### 5.3 Negative Sampling in Multi-Modal Recommendation Systems

Negative sampling is a crucial technique in recommendation systems, which helps to select the most informative negative samples from a large pool of candidates, thereby improving the performance of the recommendation model [48]. In recommendation systems, negative sampling helps to address the issue of data sparsity and improve the accuracy of recommendations [28]. The goal of negative sampling in recommendation systems is to identify the negative samples that are most similar to the positive samples, while also ensuring that the selected negative samples are diverse and representative of the entire item set [51].

One of the key challenges in negative sampling for recommendation systems is the selection of the most informative negative samples. This is because the number of possible negative samples is typically very large, and selecting the most informative ones requires careful consideration of the relationships between the different modalities [87]. To address this challenge, researchers have proposed a variety of techniques, including the use of graph-based methods [50], neural networks [46], and hybrid approaches that combine multiple techniques [42].

Another important consideration in negative sampling for recommendation systems is the issue of bias and variance. Bias refers to the systematic error introduced by the sampling method, while variance refers to the random error introduced by the sampling method [39]. To minimize bias and variance, researchers have proposed a variety of techniques, including the use of stratified sampling [49], importance sampling [141], and adaptive sampling [45].

In addition to these technical challenges, negative sampling in recommendation systems also raises a number of practical considerations. For example, the selection of negative samples must be carefully balanced against the need to minimize computational complexity and ensure scalability [14]. Furthermore, the use of negative sampling in recommendation systems must be carefully evaluated in terms of its impact on the overall performance of the system, including metrics such as accuracy, diversity, and novelty [58].

Despite these challenges, negative sampling remains a crucial technique in recommendation systems, and researchers continue to explore new and innovative approaches to improving its performance [47]. For example, recent work has focused on the use of deep learning techniques, such as neural networks and autoencoders, to improve the selection of negative samples and minimize bias and variance [142]. Other researchers have explored the use of graph-based methods and hybrid approaches to combine multiple techniques and improve the performance of negative sampling [29].

In conclusion, negative sampling is a critical component of recommendation systems, and its performance has a significant impact on the overall accuracy and diversity of recommendations [30]. While there are a number of technical and practical challenges associated with negative sampling, researchers continue to explore new and innovative approaches to improving its performance. As the field of recommendation systems continues to evolve, it is likely that negative sampling will remain a key area of research and development [34]. By providing a comprehensive overview of the current state of the art in negative sampling for recommendation systems, this subsection aims to contribute to the ongoing development of this important area of research [28].

### 5.4 Real-World Applications of Negative Sampling

Negative sampling has numerous real-world applications, including personalized advertising, content recommendation, and social network analysis. In personalized advertising, negative sampling can be used to recommend targeted ads to users based on their interests and preferences [52]. For instance, a company like Google can use negative sampling to filter out irrelevant ads and show users ads that are more likely to be of interest to them. This approach has been shown to be effective in improving the accuracy of ad recommendations and increasing user engagement [22]. By leveraging negative sampling, companies can create more effective advertising campaigns that resonate with their target audience.

In addition to personalized advertising, negative sampling is also applied in content recommendation, where it is used to recommend relevant content, such as news articles, blog posts, or videos, to users based on their past interactions [23]. For example, a news aggregator like Google News can use negative sampling to filter out irrelevant news articles and show users articles that are more likely to be of interest to them. This approach has been shown to be effective in improving the accuracy of content recommendations and increasing user engagement [27]. Moreover, negative sampling can be used in social network analysis to recommend friends, groups, or communities to users based on their social connections and interests [143]. For instance, a social media platform like Facebook can use negative sampling to filter out irrelevant friend suggestions and show users friend suggestions that are more likely to be of interest to them.

The application of negative sampling in these domains is not without challenges. One of the key challenges is the trade-off between accuracy and diversity [58]. On one hand, negative sampling can be used to improve the accuracy of recommendations by filtering out irrelevant items. On the other hand, negative sampling can also be used to improve the diversity of recommendations by showing users items that are less popular but more relevant to their interests [63]. To address this challenge, researchers have proposed various approaches, such as using multiple negative sampling strategies [48] and incorporating side information [88]. These approaches aim to balance the trade-off between accuracy and diversity, ensuring that users receive relevant and varied recommendations.

Another challenge in negative sampling is the cold start problem, where new users or items lack historical interaction data [54]. To address this challenge, researchers have proposed various approaches, such as using content-based filtering [42] and incorporating side information [111]. These approaches have been shown to be effective in improving the accuracy of recommendations for new users or items. Furthermore, researchers have also explored the use of negative sampling in addressing other challenges, such as bias and variance, which can significantly impact the performance of recommendation systems [83].

In conclusion, negative sampling has numerous real-world applications, including personalized advertising, content recommendation, and social network analysis. While there are challenges associated with negative sampling, such as the trade-off between accuracy and diversity and the cold start problem, researchers have proposed various approaches to address these challenges. As the field of recommendation systems continues to evolve, it is likely that negative sampling will play an increasingly important role in improving the accuracy and diversity of recommendations. Future research directions include exploring new negative sampling strategies, incorporating side information, and addressing the cold start problem [144]. Overall, negative sampling is a powerful technique that can be used to improve the accuracy and diversity of recommendations in various domains [110].

### 5.5 Challenges and Future Directions of Negative Sampling

Despite the effectiveness of negative sampling in improving the performance of recommendation systems, there are several challenges and future directions that need to be addressed. One of the primary challenges is improving the efficiency and scalability of negative sampling algorithms [55]. As the size of the dataset increases, the computational cost of negative sampling also increases, making it essential to develop more efficient algorithms that can handle large-scale datasets. Another challenge is the selection of informative negative samples, which is critical in improving the performance of recommendation systems [49]. The choice of negative sampling strategy can significantly impact the performance of the recommendation system, and therefore, it is essential to develop strategies that can select informative negative samples effectively.

Recent studies have shown that using techniques such as adversarial sampling and reinforcement learning-based sampling can improve the performance of negative sampling. However, these techniques are often computationally expensive and require significant computational resources. Therefore, there is a need to develop more efficient and scalable negative sampling algorithms that can handle large-scale datasets. 

Another challenge in negative sampling is the issue of bias and variance. The choice of negative sampling strategy can introduce bias and variance in the estimation of the recommendation model, which can impact the performance of the system. Therefore, it is essential to develop techniques that can mitigate bias and variance in negative sampling. 

The evaluation of negative sampling strategies is also a critical challenge. The choice of evaluation metric can significantly impact the performance of the recommendation system, and therefore, it is essential to develop evaluation metrics that can effectively evaluate the performance of negative sampling strategies. 

In terms of future directions, there are several areas that need to be explored. One area is the development of more efficient and scalable negative sampling algorithms that can handle large-scale datasets. Another area is the development of techniques that can mitigate bias and variance in negative sampling. 

In conclusion, negative sampling is a critical component of recommendation systems, and its effectiveness has a significant impact on the performance of the system. However, there are several challenges and future directions that need to be addressed, including improving the efficiency and scalability of negative sampling algorithms, selecting informative negative samples, mitigating bias and variance, and developing effective evaluation metrics. 

As [21] points out, the number of negative samples needed for effective negative sampling is still an open question. 

The use of techniques such as under-sampling and over-sampling can help mitigate the issue of class imbalance in negative sampling [60]. 

Finally, [145] and [146] demonstrate the importance of unbiased learning-to-rank algorithms and counterfactual evaluation in negative sampling. 

Overall, negative sampling is a critical component of recommendation systems, and its effectiveness has a significant impact on the performance of the system. Further research is needed to develop more efficient and effective negative sampling strategies that can improve the performance of recommendation systems [11].

## 6 Challenges and Limitations

### 6.1 Bias and Variance in Negative Sampling

The trade-off between bias and variance is a fundamental challenge in negative sampling, as it directly affects the performance of recommendation models. Understanding how different negative sampling strategies influence this trade-off is essential for optimizing model performance. [2] have shown that the choice of negative sampling strategy can significantly impact the bias-variance trade-off, and that some strategies can lead to overfitting or underfitting.

One of the key challenges in negative sampling is the selection of informative negative samples. [18] propose a stochastic negative mining approach that selects hard negative samples based on their similarity to the positive samples. This approach can help to reduce the bias in the model by selecting negative samples that are more informative. [5] also propose a mixed negative sampling approach that combines the strengths of different negative sampling strategies to reduce the bias and variance of the model.

Another challenge in negative sampling is the issue of false negatives. [133] propose a false negative elimination approach that identifies and eliminates false negative samples to improve the performance of the model. [80] also propose a meta-classifier free negative sampling approach that can help to reduce the issue of false negatives.

The bias-variance trade-off in negative sampling can also be influenced by the choice of loss function. [79] propose a contrastive loss function that uses hard negative samples to improve the performance of the model. [147] also propose a hard negative sample mining approach that uses a ranking loss function to select informative negative samples.

In addition to the choice of negative sampling strategy and loss function, the bias-variance trade-off can also be influenced by the choice of model architecture. [14] propose an efficient non-sampling factorization machine approach that can help to reduce the bias and variance of the model. [137] also propose a context-aware negative sampling approach that uses a sequential recommendation model to select informative negative samples.

Overall, the bias-variance trade-off in negative sampling is a complex issue that depends on a variety of factors, including the choice of negative sampling strategy, loss function, and model architecture. [11] provide a comprehensive review of negative sampling strategies and their applications, and highlight the importance of carefully selecting the negative sampling strategy to optimize the performance of the model.

Future research directions in negative sampling include the development of more effective negative sampling strategies that can reduce the bias and variance of the model. [148] provide a review of negative sampling strategies for contrastive representation learning, and highlight the importance of developing more effective negative sampling strategies for this task. [82] propose a layer-diverse negative sampling approach that can help to reduce the bias and variance of graph neural networks.

In conclusion, the bias-variance trade-off in negative sampling is a critical issue that affects the performance of recommendation models. Understanding how different negative sampling strategies influence this trade-off is essential for optimizing model performance. By carefully selecting the negative sampling strategy, loss function, and model architecture, it is possible to reduce the bias and variance of the model and improve its performance. [138] propose a personalized negative reservoir approach that can help to reduce the bias and variance of the model in incremental learning settings. [149] also propose a false negative estimation approach that can help to reduce the bias and variance of the model in e-commerce search settings.

### 6.2 Cold Start Problems in Negative Sampling

Cold start problems are a significant challenge in negative sampling for recommendation systems, where new users or items lack historical interaction data, making it difficult to accurately predict their preferences [28]. This issue is further complicated by the fact that negative sampling relies on the selection of informative negative samples to train the model, which can be particularly challenging when there is limited data available [26]. As discussed in the previous section, the bias-variance trade-off in negative sampling can have a significant impact on the performance of recommendation models, and addressing cold start problems is crucial to achieving optimal results.

To address these challenges, various strategies have been proposed, including the use of transfer learning [33], meta-learning [86], and hybrid approaches that combine multiple techniques [88]. One effective approach is to leverage side information, such as item attributes or user demographics, to improve the accuracy of negative sampling [83]. For example, [84] proposes a method for inferring networks of substitutable and complementary products, which can be used to improve the accuracy of negative sampling for new items.

Graph-based methods, such as graph convolutional networks, have also been proposed to model the relationships between items and users [51]. Additionally, meta-learning has been shown to be effective in improving the accuracy of negative sampling for new users and items [34]. Meta-learning involves training a model on a set of tasks, such that it can learn to adapt quickly to new tasks with limited data. This approach has been shown to be effective in improving the accuracy of negative sampling for new users and items [86].

Other strategies that can be used to address cold start problems in negative sampling include the use of pseudo-labeling, self-supervised learning, and multi-task learning. These approaches can help to improve the accuracy of negative sampling by leveraging additional information or training data. However, despite the progress that has been made in addressing cold start problems in negative sampling, there are still several challenges that need to be addressed. One of the main challenges is the lack of data available for new users and items, which can make it difficult to train accurate models. Another challenge is the need for more efficient and scalable algorithms that can handle large amounts of data and provide accurate results in real-time.

The development of more efficient and scalable algorithms for negative sampling is closely tied to the issue of computational efficiency, which is discussed in the following section. As the scale of recommendation systems grows, the computational complexity of negative sampling strategies becomes a significant bottleneck, and addressing this challenge is crucial to achieving optimal performance. By leveraging the strategies discussed in this section, such as transfer learning, meta-learning, and graph-based methods, it is possible to improve the accuracy of negative sampling in cold start scenarios, and to develop more efficient and scalable algorithms that can provide accurate results in real-time.

### 6.3 Scalability and Computational Efficiency

The scalability and computational efficiency of negative sampling methods are crucial for the practical deployment of recommendation systems. As the scale of recommendation systems grows, the computational complexity of negative sampling strategies becomes a significant bottleneck [50]. To address this challenge, various approaches have been proposed to improve the computational efficiency of negative sampling methods. One effective strategy is to use distributed computing and parallel processing techniques to speed up the computation of negative sampling [2]. 

Another approach to improve computational efficiency is to use approximations and heuristics. For example, [14] proposes a non-sampling factorization machine approach, which can reduce the computational complexity of negative sampling. Additionally, [77] suggests using popularity-aware item weighting to reduce the number of negative samples required. 

The choice of negative sampling strategy also has a significant impact on computational efficiency. For instance, [110] proposes a boolean kernel approach, which can reduce the computational complexity of negative sampling. Similarly, [45] suggests using coupled Poisson factorization, which can improve the computational efficiency of negative sampling.

Furthermore, the use of deep learning techniques can also improve the computational efficiency of negative sampling methods. For example, [42] proposes a deep autoencoder approach, which can learn compact representations of users and items, reducing the computational complexity of negative sampling. Additionally, [46] suggests using neural matrix factorization, which can improve the computational efficiency of negative sampling.

Despite these advances, there are still significant challenges to be addressed in improving the scalability and computational efficiency of negative sampling methods. One major challenge is the trade-off between model performance and computational efficiency. While approximations and heuristics can improve computational efficiency, they may also compromise model performance [39]. 

In conclusion, the scalability and computational efficiency of negative sampling methods are critical for the practical deployment of recommendation systems. Various approaches, including distributed computing, approximations, and deep learning techniques, have been proposed to improve computational efficiency. However, there are still significant challenges to be addressed, and further research is needed to develop more efficient and effective negative sampling methods. As highlighted in [29], the development of more efficient and scalable negative sampling methods is an active area of research, and new techniques and strategies are being proposed to address the challenges of scalability and computational efficiency. Ultimately, the choice of negative sampling strategy will depend on the specific requirements of the application, and a careful evaluation of the trade-offs between different approaches is essential to achieve optimal performance [30].

### 6.4 Evaluation Metrics and Negative Sampling

The evaluation of negative sampling strategies in recommendation systems is a crucial aspect that heavily influences the optimization of model performance. As discussed in the previous section, the scalability and computational efficiency of negative sampling methods are critical for the practical deployment of recommendation systems, and the choice of evaluation metrics plays a significant role in assessing their effectiveness. Understanding the interaction between different metrics and negative sampling techniques is essential for optimizing model performance, as it allows for a comprehensive evaluation of the trade-offs between accuracy and diversity.

Various metrics, such as precision, recall, F1-score, and A/B testing, are commonly used to assess the effectiveness of recommendation systems. However, the selection of appropriate metrics depends on the specific goals of the recommendation system, such as improving accuracy, diversity, or novelty. In the context of negative sampling, the evaluation metrics should account for the trade-offs between accuracy and diversity, and metrics like intra-list similarity and inter-list similarity can be used to evaluate the diversity of recommended items [22]. Moreover, metrics like precision and recall can be used to evaluate the accuracy of recommended items [23].

Recent studies have proposed various evaluation metrics for negative sampling, including metrics that account for the popularity of items [77] and metrics that account for the diversity of recommended items [63]. These metrics can be used to evaluate the effectiveness of negative sampling strategies in improving the accuracy and diversity of recommended items. Furthermore, studies have also explored the use of multi-armed bandit algorithms for evaluating negative sampling strategies [150], which can provide a more comprehensive understanding of the trade-offs between accuracy and diversity.

The evaluation of negative sampling strategies is also influenced by the type of recommendation system being used, as well as the type of negative sampling technique being employed. For instance, in the context of collaborative filtering, metrics like mean average precision and normalized discounted cumulative gain can be used to evaluate the effectiveness of negative sampling strategies [143]. In contrast, in the context of content-based filtering, metrics like precision and recall can be used to evaluate the effectiveness of negative sampling strategies [48]. Additionally, techniques like random sampling and popularity-based sampling can have different effects on the accuracy and diversity of recommended items [54], and techniques like adversarial sampling and reinforcement learning-based sampling can be used to improve the accuracy and diversity of recommended items [2].

In conclusion, the evaluation of negative sampling strategies in recommendation systems requires a comprehensive understanding of various evaluation metrics and their interactions with negative sampling techniques. By selecting appropriate evaluation metrics and negative sampling techniques, researchers and practitioners can optimize model performance and improve the accuracy and diversity of recommended items. This understanding is essential for advancing the field of recommendation systems, and future research should continue to explore the development of new evaluation metrics and negative sampling techniques, as well as their applications in various recommendation systems [26]. As noted in [58], the development of effective evaluation metrics and negative sampling techniques is crucial for improving the performance of recommendation systems, and studies like [151] and [53] have highlighted the importance of evaluating negative sampling strategies in the context of collaborative filtering and offline evaluation, ultimately informing the design of advanced negative sampling techniques discussed in the following section.

### 6.5 Advanced Negative Sampling Techniques

Recent advancements in negative sampling techniques have shown promising results in improving recommendation model performance. These techniques often leverage additional information or novel optimization strategies. For instance, [55] proposes a 2-stage negative sampling strategy which finds triplets that are highly informative for learning, allowing collaborative metric learning to work effectively even when the batch size is an order of magnitude smaller than what would be needed with the default uniform sampling. This approach highlights the importance of selecting informative negative samples to enhance model performance.

One key area of research in advanced negative sampling techniques is the development of methods that can adaptively select negative samples based on their potential impact on model performance. [21] investigates the impact of the number of negative samples on the performance of contrastive learning models, providing insights into the optimal number of negative samples required for effective learning. 

Another significant direction in advanced negative sampling techniques is the incorporation of side information, such as item attributes or user demographics, to inform the negative sampling process. [54] demonstrates the effectiveness of using side information to improve the accuracy of recommendations, particularly in cold start scenarios. 

The use of graph-based methods is also a prominent area of research in advanced negative sampling techniques. [95] proposes a symmetric metric learning approach that incorporates graph structures to model complex relationships between items, leading to improved recommendation performance.

Moreover, [59] explores the impact of sampling strategies on the performance of collaborative filtering algorithms, emphasizing the need for careful consideration of sampling methods to ensure accurate and reliable results. [61] introduces a novel optimization metric, Lower-Left Partial AUC, which is computationally efficient and strongly correlates with Top-K ranking metrics, providing a promising approach for optimizing recommendation models.

In terms of future directions, [11] provides a comprehensive review of negative sampling techniques, highlighting their significance and potential applications in various fields. 

Overall, advanced negative sampling techniques have shown significant promise in improving the performance of recommendation models. By leveraging additional information, novel optimization strategies, and careful consideration of sampling methods, these techniques can help address key challenges in recommendation systems, such as data sparsity and cold start problems.

## 7 Conclusion

In conclusion, negative sampling is a crucial component of recommendation systems, and its effectiveness has a significant impact on the accuracy and diversity of recommendations. The importance of negative sampling has been highlighted in various studies, including [3], which demonstrates the challenges of modeling the spread of influence in social networks with negative opinions.

Recent advances in negative sampling have led to the development of more efficient and effective methods, such as [4] and [78]. These methods have been shown to improve the performance of recommendation systems, particularly in cases where the number of negative samples is large. However, the choice of negative sampling strategy can have a significant impact on the performance of the system, as demonstrated in [2] and [14].

The use of negative sampling has also been explored in other areas, such as [19] and [133]. These studies demonstrate the importance of carefully selecting negative samples to improve the performance of machine learning models. Furthermore, [21] provides a theoretical analysis of the number of negative samples required for effective contrastive learning.

In addition to the technical aspects of negative sampling, it is also important to consider the practical implications of using negative sampling in real-world applications. For example, [10] demonstrates the effectiveness of negative sampling in improving the performance of personalized ranking models. Similarly, [5] shows that negative sampling can be used to improve the performance of two-tower neural networks in recommendation systems.

Despite the many advances in negative sampling, there are still several challenges and open questions that need to be addressed. For example, [15] highlights the importance of carefully selecting negative samples in hyperlink prediction tasks. Similarly, [152] demonstrates the challenges of selecting negative samples in hyperedge prediction tasks.

In terms of future directions, there are several areas that require further research. For example, [80] demonstrates the importance of developing meta-classifier-free negative sampling methods for extreme multilabel classification tasks. Similarly, [82] highlights the importance of developing layer-diverse negative sampling methods for graph neural networks.

Overall, negative sampling is a crucial component of recommendation systems, and its effectiveness has a significant impact on the accuracy and diversity of recommendations. By carefully selecting negative samples and using effective negative sampling strategies, it is possible to improve the performance of recommendation systems and address several challenges and open questions in the field. As demonstrated in [11], negative sampling is a vital component of many machine learning applications, and its importance will only continue to grow in the future. Therefore, further research is needed to develop more effective and efficient negative sampling methods, such as [136] and [137], to address the challenges and open questions in the field.

## References

[1] Notes on Noise Contrastive Estimation and Negative Sampling

[2] On Sampling Strategies for Neural Network-based Collaborative Filtering

[3] Influence Maximization in Social Networks When Negative Opinions May Emerge and Propagate

[4] Tag-Aware Personalized Recommendation Using a Deep-Semantic Similarity Model with Negative Sampling

[5] Mixed Negative Sampling for Learning Two-tower Neural Networks in Recommendations

[6] Understanding Negative Sampling in Graph Representation Learning

[7] Characterizing and Avoiding Negative Transfer

[8] Relieving popularity bias in recommendation via debiasing representation enhancement

[9] Neighborhood-based Hard Negative Mining for Sequential Recommendation

[10] Personalized Ranking with Importance Sampling

[11] Does Negative Sampling Matter? a Review With Insights Into its Theory and Applications

[12] Scaling Session-Based Transformer Recommendations using Optimized Negative Sampling and Loss Functions

[13] NGAME: Negative Mining-aware Mini-batching for Extreme Classification

[14] Efficient Non-Sampling Factorization Machines for Optimal Context-Aware Recommendation

[15] Negative Sampling for Hyperlink Prediction in Networks

[16] Asymptotically Unbiased Estimation for Delayed Feedback Modeling via Label Correction

[17] Hard Negative Sampling Strategies for Contrastive Representation Learning

[18] Stochastic Negative Mining for Learning with Large Output Spaces

[19] Neural Passage Retrieval with Improved Negative Contrast

[20] Design of Negative Sampling Strategies for Distantly Supervised Skill  Extraction

[21] Rethinking InfoNCE: How Many Negative Samples Do You Need?

[22] A Survey of Collaborative Filtering Techniques

[23] Information filtering via self-consistent refinement

[24] Statistical analysis of $k$-nearest neighbor collaborative recommendation

[25] NINU: An Incremental User-Based Algorithm for Data Sparsity Recommender Systems

[26] Deep Learning based Recommender System: A Survey and New Perspectives

[27] Solving the apparent diversity-accuracy dilemma of recommender systems

[28] Collaborative Filtering with Recurrent Neural Networks

[29] Trust your neighbors: A comprehensive survey of neighborhood-based methods for recommender systems

[30] Item Recommendation from Implicit Feedback

[31] FeedRec: News Feed Recommendation with Various User Feedbacks

[32] S-Walk: Accurate and Scalable Session-based Recommendation with Random Walks

[33] MeLU: Meta-Learned User Preference Estimator for Cold-Start Recommendation

[34] Deep Meta-learning in Recommendation Systems: A Survey

[35] The Unfairness of Popularity Bias in Recommendation

[36] Managing Popularity Bias in Recommender Systems with Personalized  Re-ranking

[37] Multi-factor Sequential Re-ranking with Perception-Aware Diversification

[38] Causal Inference in Recommender Systems: A Survey and Future Directions

[39] A Troubling Analysis of Reproducibility and Progress in Recommender Systems Research

[40] Accurate and diverse recommendations via eliminating redundant correlations

[41] Collaborative filtering and deep learning based recommendation system for cold start items

[42] Deep Auto Encoder Model With Convolutional Text Networks for Video Recommendation

[43] A Pre-Filtering Approach for Incorporating Contextual Information Into Deep Learning Based Recommender Systems

[44] Addressing Complete New Item Cold-Start Recommendation: A Niche Item-Based Collaborative Filtering via Interrelationship Mining

[45] Coupled Poisson Factorization Integrated With User/Item Metadata for Modeling Popular and Sparse Ratings in Scalable Recommendation

[46] Neural Matrix Factorization Recommendation for User Preference Prediction Based on Explicit and Implicit Feedback

[47] Deep variational models for collaborative filtering-based recommender systems

[48] Tag-Aware Personalized Recommendation Using a Hybrid Deep Model

[49] On Sampled Metrics for Item Recommendation

[50] Fast Adaptively Weighted Matrix Factorization for Recommendation with Implicit Feedback

[51] Deep Learning for Sequential Recommendation: Algorithms, Influential  Factors, and Evaluations

[52] Seeing stars: Exploiting class relationships for sentiment  categorization with respect to rating scales

[53] Reducing Offline Evaluation Bias in Recommendation Systems

[54] A collaborative filtering approach to mitigate the new user cold start problem

[55] Improving Collaborative Metric Learning with Efficient Negative Sampling

[56] A probabilistic model to resolve diversity–accuracy challenge of recommendation systems

[57] Balancing Unobserved Confounding with a Few Unbiased Ratings in Debiased Recommendations

[58] A Survey on Recommendation Methods Beyond Accuracy

[59] On Sampling Collaborative Filtering Datasets

[60] Entropy and improved k‐nearest neighbor search based under‐sampling (ENU) method to handle class overlap in imbalanced datasets

[61] Lower-Left Partial AUC: An Effective and Efficient Optimization Metric for Recommendation

[62] Revisiting Alternative Experimental Settings for Evaluating Top-N Item Recommendation Algorithms

[63] Recent Advances in Diversified Recommendation

[64] Using Posters to Recommend Anime and Mangas in a Cold-Start Scenario

[65] Cold-start Sequential Recommendation via Meta Learner

[66] Sequential Recommendation for Cold-start Users with Meta Transitional Learning

[67] KGBoost: A Classification-based Knowledge Base Completion Method with Negative Sampling

[68] Improving Knowledge Graph Completion with Generative Hard Negative Mining

[69] MetaKG: Meta-Learning on Knowledge Graph for Cold-Start Recommendation

[70] Task-adaptive Neural Process for User Cold-Start Recommendation

[71] A Survey on Negative Transfer

[72] Negative Sampling in Knowledge Graph Representation Learning: A Review

[73] Stabilized Doubly Robust Learning for Recommendation on Data Missing Not at Random

[74] Meta-Learning with Adaptive Weighted Loss for Imbalanced Cold-Start Recommendation

[75] Generative Adversarial Zero-Shot Learning for Cold-Start News Recommendation

[76] Sampling from a couple of negatively correlated gamma variates

[77] Popularity-Aware Item Weighting for Long-Tail Recommendation

[78] Analysis of the Impact of Negative Sampling on Link Prediction in  Knowledge Graphs

[79] Contrastive Learning with Hard Negative Samples

[80] Meta-classifier free negative sampling for extreme multilabel classification

[81] Bayesian Negative Sampling for Recommendation

[82] Layer-diverse Negative Sampling for Graph Neural Networks

[83] Research Commentary on Recommendations with Side Information: A Survey and Research Directions

[84] Inferring Networks of Substitutable and Complementary Products

[85] Tenrec: A Large-scale Multipurpose Benchmark Dataset for Recommender Systems

[86] Learning to Learn a Cold-start Sequential Recommender

[87] Multi-Component Graph Convolutional Collaborative Filtering

[88] Collaborative Filtering with Social Exposure: A Modular Approach to Social Recommendation

[89] Criterion-based Heterogeneous Collaborative Filtering for Multi-behavior Implicit Recommendation

[90] GRAPH-BASED RECOMMENDATION SYSTEM

[91] Recurrent Naive Bayes for Multi-Criteria Recommender Systems: A Novel Approach for Partial Preference Imputation

[92] Multi-sided Exposure Bias in Recommendation

[93] A Survey on Dropout Methods and Experimental Verification in Recommendation

[94] The influence of negative training set size on machine learning-based virtual screening

[95] Symmetric Metric Learning with Adaptive Margin for Recommendation

[96] Elliot: A Comprehensive and Rigorous Framework for Reproducible Recommender Systems Evaluation

[97] KuaiRec: A Fully-observed Dataset and Insights for Evaluating Recommender Systems

[98] Efficient Heterogeneous Collaborative Filtering without Negative Sampling for Recommendation

[99] Fast Matrix Factorization for Online Recommendation with Implicit Feedback

[100] Latent Contextual Bandits and their Application to Personalized  Recommendations for New Users

[101] ML2E: Meta-Learning Embedding Ensemble for Cold-Start Recommendation

[102] Cascading Bandits for Large-Scale Recommendation Problems

[103] Neural Interactive Collaborative Filtering

[104] Diffusion Augmentation for Sequential Recommendation

[105] Cluster Anchor Regularization to Alleviate Popularity Bias in Recommender Systems

[106] Uncovering the Deep Filter Bubble: Narrow Exposure in Short-Video Recommendation

[107] Breaking Feedback Loops in Recommender Systems with Causal Inference

[108] Learning to Recommend Accurate and Diverse Items

[109] Latent multi-criteria ratings for recommendations

[110] Boolean kernels for collaborative filtering in top-N item recommendation

[111] Addressing the Item Cold-start Problem by Attribute-driven Active  Learning

[112] Leveraging post-click feedback for content recommendations

[113] HAES: A New Hybrid Approach for Movie Recommendation with Elastic Serendipity

[114] Song recommendation with non-negative matrix factorization and graph total variation

[115] Reconciling the Accuracy-Diversity Trade-off in Recommendations

[116] Filter Bubble or Homogenization? Disentangling the Long-Term Effects of Recommendations on User Consumption Patterns

[117] The Stereotyping Problem in Collaboratively Filtered Recommender Systems

[118] Going Beyond Popularity and Positivity Bias: Correcting for Multifactorial Bias in Recommender Systems

[119] Evaluation of recommendations: rating-prediction and ranking

[120] Unbiased offline recommender evaluation for missing-not-at-random implicit feedback

[121] Off-policy evaluation for slate recommendation

[122] On (Normalised) Discounted Cumulative Gain as an Off-Policy Evaluation Metric for Top-n Recommendation

[123] User-centered Evaluation of Popularity Bias in Recommender Systems

[124] Bias and Debias in Recommender System: A Survey and Future Directions

[125] Exploring Data Splitting Strategies for the Evaluation of Recommendation Models

[126] Towards Confidence-aware Calibrated Recommendation

[127] FPAdaMetric: False-Positive-Aware Adaptive Metric Learning for Session-Based Recommendation

[128] A Case Study on Sampling Strategies for Evaluating Neural Sequential Item Recommendation Models

[129] Improving Cold Start Stereotype-Based Recommendation Using Deep Learning

[130] Simplify and Robustify Negative Sampling for Implicit Collaborative  Filtering

[131] Double Correction Framework for Denoising Recommendation

[132] Rethinking Missing Data: Aleatoric Uncertainty-Aware Recommendation

[133] Your Negative May not Be True Negative: Boosting Image-Text Matching with False Negative Elimination

[134] gSASRec: Reducing Overconfidence in Sequential Recommendation Trained with Negative Sampling

[135] On the Theories Behind Hard Negative Sampling for Recommendation

[136] Synthetic Hard Negative Samples for Contrastive Learning

[137] Context-Aware Negative Sampling for Sequential Recommendation

[138] Personalized Negative Reservoir for Incremental Learning in Recommender Systems

[139] Novel Recommendation System for Tourist Spots Based on Hierarchical Sampling Statistics and SVD++

[140] Fusing Similarity Models with Markov Chains for Sparse Sequential Recommendation

[141] Improving One-Class Collaborative Filtering via Ranking-Based Implicit Regularizer

[142] Deep Learning Modeling for Top-N Recommendation With Interests Exploring

[143] Collaborative filtering via graph signal processing

[144] Using Stable Matching to Optimize the Balance between Accuracy and Diversity in Recommendation

[145] Unbiased LambdaMART: An Unbiased Pairwise Learning-to-Rank Algorithm

[146] Counterfactual Evaluation of Slate Recommendations with Sequential Reward Interactions

[147] Hard Negative Sample Mining for Whole Slide Image Classification

[148] Negative Sampling for Contrastive Representation Learning: A Review

[149] Mitigating Pooling Bias in E-commerce Search via False Negative Estimation

[150] Online Collaborative Filtering on Graphs

[151] Using Collaborative Filtering to Overcome the Curse of Dimensionality when Clustering Users in a Group Recommender System

[152] AHP: Learning to Negative Sample for Hyperedge Prediction

