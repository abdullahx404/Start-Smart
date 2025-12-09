import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/selection_provider.dart';
import '../utils/colors.dart';
import '../utils/constants.dart';

/// Filter panel for selecting neighborhood and category
class FilterPanel extends ConsumerWidget {
  const FilterPanel({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final selectedNeighborhood = ref.watch(selectedNeighborhoodProvider);
    final isExpanded = ref.watch(filterPanelExpandedProvider);

    return AnimatedContainer(
      duration: UIConstants.mediumAnimation,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Collapsed header (always visible)
          InkWell(
            onTap: () {
              ref.read(filterPanelExpandedProvider.notifier).state =
                  !isExpanded;
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.filter_list, color: AppColors.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          selectedNeighborhood != null
                              ? Neighborhoods.getDisplayName(
                                  selectedNeighborhood,
                                )
                              : 'Select Neighborhood',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          '${Categories.getIcon(selectedCategory)} ${Categories.getDisplayName(selectedCategory)}',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    isExpanded ? Icons.expand_less : Icons.expand_more,
                    color: AppColors.textSecondary,
                  ),
                ],
              ),
            ),
          ),

          // Expanded content
          if (isExpanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Category selection
                  const Text(
                    'Business Category',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                  const SizedBox(height: 8),
                  _CategorySelector(
                    selectedCategory: selectedCategory,
                    onCategoryChanged: (category) {
                      ref.read(selectedCategoryProvider.notifier).state =
                          category;
                    },
                  ),
                  const SizedBox(height: 16),

                  // Neighborhood selection
                  const Text(
                    'Neighborhood',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                  const SizedBox(height: 8),
                  _NeighborhoodSelector(
                    selectedNeighborhood: selectedNeighborhood,
                    onNeighborhoodChanged: (neighborhood) {
                      ref.read(selectedNeighborhoodProvider.notifier).state =
                          neighborhood;
                    },
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Category toggle buttons
class _CategorySelector extends StatelessWidget {
  final String selectedCategory;
  final Function(String) onCategoryChanged;

  const _CategorySelector({
    required this.selectedCategory,
    required this.onCategoryChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: Categories.all.map((category) {
        final isSelected = category == selectedCategory;
        return Expanded(
          child: Padding(
            padding: EdgeInsets.only(
              right: category != Categories.all.last ? 8 : 0,
            ),
            child: InkWell(
              onTap: () => onCategoryChanged(category),
              borderRadius: BorderRadius.circular(8),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: isSelected
                      ? AppColors.primary.withValues(alpha: 0.1)
                      : AppColors.surfaceVariant,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isSelected
                        ? AppColors.primary
                        : AppColors.surfaceVariant,
                    width: isSelected ? 2 : 1,
                  ),
                ),
                child: Column(
                  children: [
                    Text(
                      Categories.getIcon(category),
                      style: const TextStyle(fontSize: 24),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      category,
                      style: TextStyle(
                        fontWeight: isSelected
                            ? FontWeight.bold
                            : FontWeight.normal,
                        color: isSelected
                            ? AppColors.primary
                            : AppColors.textPrimary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

/// Neighborhood dropdown/chips
class _NeighborhoodSelector extends StatelessWidget {
  final String? selectedNeighborhood;
  final Function(String) onNeighborhoodChanged;

  const _NeighborhoodSelector({
    required this.selectedNeighborhood,
    required this.onNeighborhoodChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: Neighborhoods.all.entries.map((entry) {
        final isSelected = entry.key == selectedNeighborhood;
        return FilterChip(
          label: Text(entry.value),
          selected: isSelected,
          onSelected: (_) => onNeighborhoodChanged(entry.key),
          selectedColor: AppColors.primary.withValues(alpha: 0.2),
          checkmarkColor: AppColors.primary,
          labelStyle: TextStyle(
            color: isSelected ? AppColors.primary : AppColors.textPrimary,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            fontSize: 12,
          ),
        );
      }).toList(),
    );
  }
}

/// Compact filter bar for use in app bars
class CompactFilterBar extends ConsumerWidget {
  const CompactFilterBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final selectedNeighborhood = ref.watch(selectedNeighborhoodProvider);

    return Row(
      children: [
        // Category dropdown
        _CompactDropdown(
          icon: Categories.getIcon(selectedCategory),
          value: selectedCategory,
          items: Categories.all,
          onChanged: (value) {
            if (value != null) {
              ref.read(selectedCategoryProvider.notifier).state = value;
            }
          },
        ),
        const SizedBox(width: 8),
        // Neighborhood dropdown
        _CompactDropdown(
          icon: '📍',
          value: selectedNeighborhood,
          items: Neighborhoods.all.keys.toList(),
          itemLabels: Neighborhoods.all,
          hint: 'Select Area',
          onChanged: (value) {
            if (value != null) {
              ref.read(selectedNeighborhoodProvider.notifier).state = value;
            }
          },
        ),
      ],
    );
  }
}

/// Compact dropdown widget
class _CompactDropdown extends StatelessWidget {
  final String icon;
  final String? value;
  final List<String> items;
  final Map<String, String>? itemLabels;
  final String? hint;
  final Function(String?) onChanged;

  const _CompactDropdown({
    required this.icon,
    required this.value,
    required this.items,
    this.itemLabels,
    this.hint,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.surfaceVariant),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(icon, style: const TextStyle(fontSize: 16)),
          const SizedBox(width: 4),
          DropdownButton<String>(
            value: value,
            hint: hint != null
                ? Text(hint!, style: const TextStyle(fontSize: 13))
                : null,
            underline: const SizedBox(),
            isDense: true,
            icon: const Icon(Icons.arrow_drop_down, size: 20),
            style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
            items: items.map((item) {
              final label = itemLabels?[item] ?? item;
              return DropdownMenuItem(value: item, child: Text(label));
            }).toList(),
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
